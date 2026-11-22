"""Compare public results with independent reference tools."""

import json
import sys
from importlib.metadata import version
from pathlib import Path

import nltk  # type: ignore[import-untyped]
import pytest
import textstat  # type: ignore[import-untyped]

from slop_away import Config, check_files, grade_sections, sync_packages
from slop_away.markdown import parse_document
from tests.corpus_support import CORPUS_ROOT
from tests.harnesses import CliHarness

DOCUMENTS = tuple(
    path
    for group in ("bad", "fixed", "good")
    for path in sorted((CORPUS_ROOT / group).glob("*.md"))
)
RULES = Path(__file__).parent / "rules"


@pytest.fixture(scope="session")
def references():
    """GIVEN pinned reference tools WHEN compared THEN stay offline."""
    data = Path(sys.prefix) / "share/nltk_data"
    marker = data / "corpora/cmudict/edition.txt"
    if not marker.is_file() or marker.read_text() != version("cmudict"):
        raise RuntimeError(
            "Run bash tests/differential/install_references.sh .venv."
        )
    nltk.data.path.insert(0, str(data))
    nltk.data.find("corpora/cmudict")
    textstat.set_lang("en_US")
    result = CliHarness(Path.cwd()).run(["vale", "--version"])
    if result.returncode or result.stdout.strip() != "vale version 3.28.1":
        raise RuntimeError("Install the pinned Vale 3.28.1 reference.")


@pytest.fixture(
    params=DOCUMENTS, ids=lambda path: f"{path.parent.name}/{path.name}"
)
def readability_case(request, references):
    """GIVEN corpus prose WHEN scored THEN compare against textstat."""
    text = request.param.read_text(encoding="utf-8")
    sections = grade_sections(text)
    expected = [
        textstat.flesch_kincaid_grade(section.prose) for section in sections
    ]
    return text, pytest.approx(expected, abs=0.5, rel=0)


def test_readability_reference(readability_case):
    """GIVEN corpus sections WHEN scored THEN stay within half a grade."""
    text, expected = readability_case
    actual = [float(section.grade) for section in grade_sections(text)]
    assert actual == expected


@pytest.fixture(
    params=DOCUMENTS, ids=lambda path: f"{path.parent.name}/{path.name}"
)
def vale_case(request, references, tmp_path, package_server):
    """GIVEN four Vale rule types WHEN compared THEN use the same sources."""
    rules = {
        path.name: path.read_bytes() for path in sorted(RULES.glob("*.yml"))
    }
    package_server.store(
        "validation",
        {f"validation/{name}": source for name, source in rules.items()},
    )
    config = Config(
        root=tmp_path,
        packages=[package_server.url("validation")],
        select=["validation"],
    )
    sync_packages(config)
    package_server.stop()
    styles = tmp_path / "styles/validation"
    styles.mkdir(parents=True)
    for name, source in rules.items():
        (styles / name).write_bytes(source)
    ini = tmp_path / ".vale.ini"
    ini.write_text(
        "StylesPath = styles\nMinAlertLevel = suggestion\n\n"
        "[*.md]\nBasedOnStyles = validation\n"
    )
    target = tmp_path / request.param.name
    source = request.param.read_text(encoding="utf-8")
    target.write_text(source, encoding="utf-8")
    reference = tmp_path / "reference" / target.name
    reference.parent.mkdir()
    characters = [char if char.isspace() else " " for char in source]
    if target.name not in config.instruction_files:
        prose = parse_document(source).prose
        for index, (char, offset) in enumerate(
            zip(prose.text, prose.offsets, strict=True)
        ):
            end = (
                prose.offsets[index + 1]
                if index + 1 < len(prose.offsets)
                else len(source)
            )
            if not char.isspace() and end > offset:
                characters[offset:end] = source[offset:end]
    reference.write_text("".join(characters), encoding="utf-8")
    arguments = [
        "vale",
        "--config",
        str(ini),
        "--output=JSON",
        "--no-exit",
        str(reference),
    ]
    result = CliHarness(tmp_path).run(arguments)
    result.check_returncode()
    records = [
        record
        for values in json.loads(result.stdout).values()
        for record in values
    ]
    expected = sorted((record["Check"], record["Line"]) for record in records)
    return target, config, expected


def test_vale_reference(vale_case):
    """GIVEN corpus documents WHEN checked THEN match Vale codes and lines."""
    path, config, expected = vale_case
    findings = check_files([path], config)
    actual = sorted((finding.code, finding.line) for finding in findings)
    assert actual == expected
