"""Test baseline records and adoption command behavior."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from slop_away import (
    Baseline,
    Config,
    check_text,
    load_baseline,
    render_findings,
    write_baseline,
)


@pytest.fixture(
    params=[
        ("\n\nYou must run the tool.", "a.md", True),
        ("You  must run the tool.", "a.md", True),
        ("YOU MUST RUN THE TOOL.", "a.md", True),
        ("You must run another tool.", "a.md", False),
        ("You must run the tool.", "b.md", False),
    ]
)
def fingerprint_case(request, tmp_path):
    """GIVEN known text WHEN compared THEN use context and path only."""
    text, path, expected = request.param
    config = Config(root=tmp_path, select=["INJ001"])
    baseline = Baseline.build(
        check_text("You must run the tool.", "a.md", config)
    )
    finding = check_text(text, path, config)[0]
    return baseline, finding, expected


def test_baseline_matches_context(fingerprint_case):
    """GIVEN a baseline WHEN matching THEN ignore location and case."""
    baseline, finding, expected = fingerprint_case
    actual = baseline.matches(finding)
    assert actual is expected


@pytest.fixture
def baseline_records(tmp_path):
    """GIVEN repeated findings WHEN saved THEN use unique sorted records."""
    config = Config(root=tmp_path, select=["INJ001"])
    first = check_text("You must run the tool.", "z.md", config)
    second = check_text("You must stop the tool.", "a.md", config)
    findings = first + second + first
    expected = {
        "version": 1,
        "fingerprints": sorted({item.fingerprint for item in findings}),
    }
    return tmp_path, findings, expected


def test_write_baseline_records(baseline_records):
    """GIVEN findings WHEN saved THEN write unique sorted fingerprints."""
    root, findings, expected = baseline_records
    write_baseline(root, findings)
    actual = json.loads((root / "slop_away.baseline.json").read_text())
    assert actual == expected


@pytest.fixture
def stored_baseline(baseline_records):
    """GIVEN a saved baseline WHEN loaded THEN retain all records."""
    root, findings, _expected = baseline_records
    expected = write_baseline(root, findings)
    return root, expected


def test_load_baseline_round_trip(stored_baseline):
    """GIVEN saved records WHEN loaded THEN return the same baseline."""
    root, expected = stored_baseline
    actual = load_baseline(root)
    assert actual == expected


@pytest.fixture
def absent_baseline(tmp_path):
    """GIVEN no baseline WHEN loaded THEN use an empty baseline."""
    return tmp_path, Baseline()


def test_missing_baseline(absent_baseline):
    """GIVEN no saved records WHEN loaded THEN return an empty baseline."""
    root, expected = absent_baseline
    actual = load_baseline(root)
    assert actual == expected


@pytest.fixture(
    params=[
        b"",
        b"invalid",
        b"[]",
        b"null",
        b"\xff",
        b'{"version": 2, "fingerprints": []}',
        b'{"version": true, "fingerprints": []}',
        b'{"version": 1, "fingerprints": {}, "extra": 1}',
        b'{"version": 1, "fingerprints": [1]}',
        b'{"version": 1, "fingerprints": ["bad"]}',
        b'{"version": 1, "version": 1, "fingerprints": []}',
    ]
)
def malformed_baseline(request, tmp_path):
    """GIVEN invalid records WHEN loaded THEN reject the baseline."""
    (tmp_path / "slop_away.baseline.json").write_bytes(request.param)
    return tmp_path, "slop_away.baseline.json"


def test_invalid_baseline(malformed_baseline):
    """GIVEN invalid data WHEN loaded THEN name the baseline file."""
    root, expected = malformed_baseline
    with pytest.raises(ValueError) as error:
        load_baseline(root)
    assert expected in str(error.value)


@pytest.fixture(params=["absolute", "parent", "digest", "code", "duplicate"])
def invalid_record(request, tmp_path):
    """GIVEN an invalid fingerprint WHEN loaded THEN reject the record."""
    digest = "a" * 64
    records = {
        "absolute": f"INJ001:/a.md:{digest}",
        "parent": f"INJ001:../a.md:{digest}",
        "digest": "INJ001:a.md:123",
        "code": f"bad code:a.md:{digest}",
        "duplicate": f"INJ001:a.md:{digest}",
    }
    values = [records[request.param]] * (
        2 if request.param == "duplicate" else 1
    )
    (tmp_path / "slop_away.baseline.json").write_text(
        json.dumps({"version": 1, "fingerprints": values})
    )
    return tmp_path, ValueError


def test_invalid_baseline_fingerprint(invalid_record):
    """GIVEN invalid fingerprints WHEN loaded THEN fail fast."""
    root, expected = invalid_record
    with pytest.raises(ValueError) as error:
        load_baseline(root)
    assert type(error.value) is expected


@pytest.fixture
def absolute_case(tmp_path):
    """GIVEN an absolute path WHEN checked THEN use a project path."""
    config = Config(root=tmp_path, select=["INJ001"])
    relative = check_text("You must run the tool.", "docs/a.md", config)
    return tmp_path / "docs/a.md", config, relative


def test_absolute_fingerprint_path(absolute_case):
    """GIVEN an absolute source path WHEN checked THEN keep its identity."""
    path, config, expected = absolute_case
    actual = check_text("You must run the tool.", path, config)
    assert actual == expected


@pytest.fixture(params=[False, True])
def baseline_cli(request, cli):
    """GIVEN old and new findings WHEN checked THEN report only new ones."""
    (cli.root / "slop_away.toml").write_text('select = ["INJ001"]\n')
    old = "You must run the tool.\n"
    (cli.root / "a.md").write_text(old)
    cli.run(
        ["slop_away", "check", "a.md", "--write-baseline"]
    ).check_returncode()
    if request.param:
        (cli.root / "a.md").write_text(old + "\nYou must stop the tool.\n")
    expected = (int(request.param), 1 if request.param else 0, "")
    return cli, expected


def test_baseline_filters_json_output(baseline_cli):
    """GIVEN a baseline WHEN checked THEN report only new JSON findings."""
    cli, expected = baseline_cli
    result = cli.run(["slop_away", "check", "a.md", "--output-format", "json"])
    actual = result.returncode, len(json.loads(result.stdout)), result.stderr
    assert actual == expected


@pytest.fixture
def invalid_fix_baseline(cli):
    """GIVEN an invalid baseline WHEN fixing THEN preserve source files."""
    source = "The tool doesn't run twice."
    (cli.root / "a.md").write_text(source)
    (cli.root / "slop_away.baseline.json").write_text("invalid")
    return cli, (2, source, "")


def test_invalid_baseline_blocks_fix_writes(invalid_fix_baseline):
    """GIVEN invalid baseline data WHEN fixing THEN write no source."""
    cli, expected = invalid_fix_baseline
    result = cli.run(["slop_away", "check", "a.md", "--fix"])
    actual = result.returncode, (cli.root / "a.md").read_text(), result.stdout
    assert actual == expected


@pytest.fixture
def refresh_case(cli):
    """GIVEN an invalid snapshot WHEN refreshed THEN replace its records."""
    (cli.root / "a.md").write_text("The tool doesn't run twice.")
    (cli.root / "slop_away.baseline.json").write_text("invalid")
    return cli, {"version": 1, "fingerprints": []}


def test_write_baseline_after_fix(refresh_case):
    """GIVEN fix and baseline flags WHEN run THEN save remaining findings."""
    cli, expected = refresh_case
    cli.run(
        ["slop_away", "check", "a.md", "--fix", "--write-baseline"]
    ).check_returncode()
    actual = json.loads((cli.root / "slop_away.baseline.json").read_text())
    assert actual == expected


@pytest.fixture
def selected_snapshot(cli):
    """GIVEN an old snapshot WHEN refreshed THEN keep selected files only."""
    (cli.root / "slop_away.toml").write_text('select = ["INJ001"]\n')
    (cli.root / "a.md").write_text("You must run the tool.")
    (cli.root / "b.md").write_text("You must stop the tool.")
    cli.run(["slop_away", "check", ".", "--write-baseline"]).check_returncode()
    findings = check_text(
        "You must stop the tool.",
        "b.md",
        Config(root=cli.root, select=["INJ001"]),
    )
    arguments = ["slop_away", "check", "b.md", "--write-baseline"]
    path = cli.root / "slop_away.baseline.json"
    return (
        cli,
        arguments,
        path,
        sorted(finding.fingerprint for finding in findings),
    )


def test_baseline_refresh_replaces_selected_snapshot(selected_snapshot):
    """GIVEN a partial refresh WHEN saved THEN replace old entries."""
    cli, arguments, path, expected = selected_snapshot
    cli.run(arguments).check_returncode()
    actual = json.loads(path.read_text())["fingerprints"]
    assert actual == expected


@pytest.fixture
def rejected_snapshot(report_case, tmp_path):
    """GIVEN invalid findings WHEN saving THEN preserve the prior file."""
    path = tmp_path / "slop_away.baseline.json"
    original = b"Existing baseline contents."
    path.write_bytes(original)
    findings = [replace(report_case[0][0], fingerprint="invalid")]
    return tmp_path, path, findings, original


def test_invalid_snapshot_preserves_baseline(rejected_snapshot):
    """GIVEN an invalid fingerprint WHEN saved THEN keep the old file."""
    root, path, findings, expected = rejected_snapshot
    with pytest.raises(ValueError):
        write_baseline(root, findings)
    assert path.read_bytes() == expected


@pytest.fixture
def raw_api_case(report_case, tmp_path):
    """GIVEN stored findings WHEN the API checks THEN return raw findings."""
    findings, _expected = report_case
    write_baseline(tmp_path, findings)
    config = Config(root=tmp_path, select=["INJ001"])
    return config, findings


def test_python_checks_keep_raw_findings(raw_api_case):
    """GIVEN a baseline WHEN Python checks run THEN keep known findings."""
    config, expected = raw_api_case
    actual = check_text("You must run the tool.", "docs/é.md", config)
    assert actual == expected


@pytest.fixture
def report_case(tmp_path):
    """GIVEN a finding WHEN rendered THEN retain every public field."""
    finding = check_text(
        "You must run the tool.",
        "docs/é.md",
        Config(root=tmp_path, select=["INJ001"]),
    )[0]
    expected = [
        {
            "code": finding.code,
            "path": "docs/é.md",
            "line": finding.line,
            "column": finding.column,
            "message": finding.message,
            "hint": finding.hint,
            "fingerprint": finding.fingerprint,
        }
    ]
    return [finding], expected


def test_json_finding_fields(report_case):
    """GIVEN a finding WHEN rendered as JSON THEN include its contract."""
    findings, expected = report_case
    actual = render_findings(findings, "json")
    assert json.loads(actual) == expected


@pytest.fixture
def annotation_case(report_case):
    """GIVEN command separators WHEN rendered THEN escape their values."""
    finding = replace(
        report_case[0][0],
        path=Path("a,b:c%\r\n.md"),
        message="Bad %\r\n::error::another command",
    )
    expected = (
        "::error file=a%2Cb%3Ac%25%0D%0A.md,line=1,col=1,"
        "title=INJ001::Bad %25%0D%0A::error::another command\n"
    )
    return [finding], expected


def test_github_annotation_escaping(annotation_case):
    """GIVEN command characters WHEN rendered THEN keep one annotation."""
    findings, expected = annotation_case
    actual = render_findings(findings, "github")
    assert actual == expected


@pytest.fixture(
    params=[("text", ""), ("agent", ""), ("github", ""), ("json", "[]\n")]
)
def empty_report(request):
    """GIVEN no findings WHEN rendered THEN use an empty report."""
    return request.param


def test_empty_reports(empty_report):
    """GIVEN no findings WHEN rendered THEN use the format's empty value."""
    output_format, expected = empty_report
    actual = render_findings([], output_format)
    assert actual == expected


@pytest.fixture
def unknown_format():
    """GIVEN an unknown format WHEN rendered THEN reject the format."""
    return "unknown", ValueError


def test_unknown_report_format(unknown_format):
    """GIVEN an unknown output format WHEN rendered THEN fail fast."""
    output_format, expected = unknown_format
    with pytest.raises(ValueError) as error:
        render_findings([], output_format)
    assert type(error.value) is expected
