"""Test the installed package."""

import tomllib
from pathlib import Path

import pytest

from slop_away.cli import main
from tests.harnesses import ApiHarness, CliHarness


@pytest.fixture
def version_case():
    """GIVEN package metadata WHEN version is requested THEN use that value."""
    root = Path(__file__).resolve().parents[1]
    with (root / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)
    version = project["project"]["version"]
    return ["slop_away", "--version"], (0, f"{version}\n", "")


@pytest.fixture
def help_case():
    """GIVEN no arguments WHEN the command runs THEN print help and exit 0."""
    return [], "usage: slop_away", (0, True, "")


def test_installed_version(cli: CliHarness, version_case):
    """GIVEN the package WHEN version is requested THEN print its version."""
    arguments, expected = version_case
    result = cli.run(arguments)
    actual = result.returncode, result.stdout, result.stderr
    assert actual == expected


def test_empty_arguments(api: ApiHarness, help_case, capsys):
    """GIVEN no arguments WHEN the command runs THEN print help and exit 0."""
    arguments, prefix, expected = help_case
    result = api.call(main, arguments)
    output = capsys.readouterr()
    actual = result, output.out.startswith(prefix), output.err
    assert actual == expected
