"""Test the version command."""

import re
import shlex
from subprocess import CompletedProcess

from pytest_bdd import parsers, scenario, then, when

from tests.harnesses import CliHarness


@scenario("features/cli.feature", "--version prints the version")
def test_version():
    """GIVEN the package WHEN version is requested THEN show the version."""


@when(parsers.parse('I run "{command}"'), target_fixture="result")
def run_command(cli: CliHarness, command: str) -> CompletedProcess[str]:
    """GIVEN a command WHEN it runs THEN collect its result."""
    return cli.run(shlex.split(command))


@then(parsers.parse("the exit code is {expected:d}"))
def check_exit(result: CompletedProcess[str], expected: int):
    """GIVEN a result WHEN the command ends THEN check its exit code."""
    actual = result.returncode
    assert actual == expected, f"Expected exit code {expected}; got {actual}."


@then(parsers.parse('stdout matches "{pattern}"'))
def check_stdout(result: CompletedProcess[str], pattern: str):
    """GIVEN output WHEN a pattern is specified THEN check the output."""
    actual = result.stdout
    assert re.fullmatch(pattern, actual.rstrip("\n")), (
        f"Expected stdout to match {pattern!r}; got {actual!r}."
    )
