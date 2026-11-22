"""Check the five stated properties through public contracts."""

import re
import tempfile
from pathlib import Path
from typing import Literal

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from slop_away import Baseline, Config, apply_fixes, check_files, check_text
from tests.harnesses import CliHarness

EXCLUDED: tuple[Literal["Cs"], ...] = ("Cs",)
TEXT = st.text(
    alphabet=st.characters(exclude_categories=EXCLUDED), max_size=200
)
PROPERTY = settings(
    max_examples=40,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)


@pytest.fixture
def safe_case(tmp_path):
    """GIVEN arbitrary text WHEN fixed again THEN use its first fix result."""
    config = Config(root=tmp_path)

    def prepare(text):
        """GIVEN text WHEN the second pass runs THEN retain the first pass."""
        return apply_fixes(text, "a.md", config), config

    return prepare


@PROPERTY
@given(TEXT)
def test_safe_fix_idempotence(safe_case, text):
    """GIVEN arbitrary text WHEN safely fixed twice THEN keep the same text."""
    expected, config = safe_case(text)
    actual = apply_fixes(expected, "a.md", config)
    assert actual == expected


@pytest.fixture
def moved_case(tmp_path):
    """GIVEN known findings WHEN lines move THEN retain their identity."""
    config = Config(root=tmp_path, select=["INJ001"])
    text = "You must run the tool."
    baseline = Baseline.build(check_text(text, "a.md", config))

    def prepare(lines):
        """GIVEN inserted lines WHEN compared THEN use the moved finding."""
        finding = check_text("Intro line.\n" * lines + text, "a.md", config)[0]
        return baseline, finding, True

    return prepare


@PROPERTY
@given(st.integers(min_value=0, max_value=100))
def test_baseline_survives_line_moves(moved_case, lines):
    """GIVEN inserted lines WHEN a baseline matches THEN retain the match."""
    baseline, finding, expected = moved_case(lines)
    actual = baseline.matches(finding)
    assert actual is expected


@pytest.fixture
def fenced_case(tmp_path):
    """GIVEN code changes WHEN checked THEN keep outside findings intact."""
    config = Config(root=tmp_path)

    def prepare(before, after):
        """GIVEN code contents WHEN checked THEN use a closed fence."""
        runs = [
            len(match[0])
            for value in (before, after)
            for match in re.finditer(r"`+", value)
        ]
        fence = "`" * (max([2, *runs]) + 1)
        prefix = "# Guide\n\nYou must run the tool.\n\n" + fence + "\n"
        old = prefix + before + "\n" + fence + "\n"
        changed = prefix + after + "\n" + fence + "\n"
        return changed, config, check_text(old, "a.md", config)

    return prepare


@PROPERTY
@given(TEXT, TEXT)
def test_fenced_code_does_not_change_findings(fenced_case, before, after):
    """GIVEN changed fenced code WHEN checked THEN keep prose findings."""
    text, config, expected = fenced_case(before, after)
    actual = check_text(text, "a.md", config)
    assert actual == expected


@pytest.fixture
def process_case(tmp_path):
    """GIVEN arbitrary bytes WHEN checked THEN use a fresh input project."""

    def prepare(source):
        """GIVEN input bytes WHEN run THEN isolate this example's files."""
        root = Path(tempfile.mkdtemp(dir=tmp_path))
        (root / ".git").mkdir()
        (root / "a.md").write_bytes(source)
        return CliHarness(root), ["slop_away", "check", "a.md"], {0, 1, 2}

    return prepare


@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    st.one_of(
        TEXT.map(lambda value: value.encode("utf-8")), st.binary(max_size=200)
    )
)
def test_arbitrary_input_has_a_defined_exit(process_case, source):
    """GIVEN any input WHEN the CLI checks THEN return a defined exit code."""
    cli, arguments, expected = process_case(source)
    result = cli.run(arguments)
    assert result.returncode in expected


@pytest.fixture
def ordered_case(tmp_path):
    """GIVEN input file orders WHEN checked THEN use the same project."""
    repeated = "The tool reads every source file before it checks the text.\n"
    texts = {
        "a.md": "You must run the tool.\n",
        "b.md": repeated,
        "c.md": repeated,
    }
    for name, source in texts.items():
        (tmp_path / name).write_text(source)
    config = Config(root=tmp_path)
    return config, check_files(list(texts), config)


@PROPERTY
@given(st.permutations(("a.md", "b.md", "c.md")))
def test_file_order_does_not_change_findings(ordered_case, paths):
    """GIVEN any file order WHEN checked THEN return the same findings."""
    config, expected = ordered_case
    actual = check_files(paths, config)
    assert actual == expected
