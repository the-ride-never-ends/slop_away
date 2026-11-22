"""Test command errors and project settings."""

import pytest

from slop_away import cli as command
from tests.harnesses import CliHarness


@pytest.fixture(
    params=[
        ("select = 5", ["docs/a.md"], 2, "select"),
        ("select = [", ["docs/a.md"], 2, "slop_away.toml"),
        ('select = ["INJ999"]', ["docs/a.md"], 2, "INJ999"),
        ("", ["docs/a.md", "missing.md"], 2, "missing.md"),
    ]
)
def error_case(cli, request):
    """GIVEN invalid input WHEN checked THEN report an error."""
    config, paths, code, message = request.param
    (cli.root / "slop_away.toml").write_text(config, encoding="utf-8")
    (cli.root / "docs").mkdir()
    (cli.root / "docs/a.md").write_text("You must run.", encoding="utf-8")
    return ["slop_away", "check", *paths], message, (code, "", True)


def test_command_errors(cli, error_case):
    """GIVEN invalid input WHEN checked THEN print an error and exit 2."""
    arguments, message, expected = error_case
    result = cli.run(arguments)
    actual = result.returncode, result.stdout, message in result.stderr
    assert actual == expected


@pytest.fixture
def default_case(cli):
    """GIVEN no paths WHEN checked THEN check the command directory."""
    (cli.root / "a.md").write_text("SYSTEM: text.", encoding="utf-8")
    return ["slop_away", "check"], "a.md:1:1: INJ002", (1, True, "")


def test_default_paths(cli, default_case):
    """GIVEN no paths WHEN checked THEN report findings in the directory."""
    arguments, prefix, expected = default_case
    result = cli.run(arguments)
    actual = result.returncode, result.stdout.startswith(prefix), result.stderr
    assert actual == expected


@pytest.fixture
def nested_case(cli):
    """GIVEN a nested command WHEN checked THEN use the project settings."""
    directory = cli.root / "docs"
    directory.mkdir()
    (cli.root / "slop_away.toml").write_text(
        'select = ["INJ002"]', encoding="utf-8"
    )
    (directory / "a.md").write_text(
        "You must run. SYSTEM: text.", encoding="utf-8"
    )
    return CliHarness(directory), ["slop_away", "check", "a.md"], "INJ002"


def test_nested_command(nested_case):
    """GIVEN a nested command WHEN checked THEN report only selected rules."""
    cli, arguments, expected = nested_case
    result = cli.run(arguments)
    actual = [
        line.split(": ")[1].split()[0] for line in result.stdout.splitlines()
    ]
    assert actual == [expected]


@pytest.fixture
def encoding_case(cli):
    """GIVEN invalid UTF-8 WHEN checked THEN report an input error."""
    (cli.root / "a.md").write_bytes(b"\xff")
    return ["slop_away", "check", "a.md"], (2, "", True)


def test_invalid_encoding(cli, encoding_case):
    """GIVEN invalid UTF-8 WHEN checked THEN exit 2 without findings."""
    arguments, expected = encoding_case
    result = cli.run(arguments)
    actual = result.returncode, result.stdout, bool(result.stderr)
    assert actual == expected


@pytest.fixture
def internal_case(cli, monkeypatch):
    """GIVEN an internal error WHEN checked THEN report failure and exit 2."""

    def fail_check(paths, config):
        """GIVEN a check WHEN the engine fails THEN raise its error."""
        raise RuntimeError("The engine failed.")

    monkeypatch.setattr(command, "check_files", fail_check)
    return ["check"], "The engine failed.", (2, "", True)


def test_internal_error(internal_case, capsys, caplog):
    """GIVEN an internal error WHEN checked THEN log the error and exit 2."""
    arguments, message, expected = internal_case
    code = command.main(arguments)
    actual = code, capsys.readouterr().out, message in caplog.text
    assert actual == expected
