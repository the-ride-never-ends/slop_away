"""Test the public test tools."""

import sys
from pathlib import Path

import pytest

from tests.harnesses import ApiHarness, CliHarness


@pytest.fixture
def api_case():
    """GIVEN arguments WHEN a function runs THEN supply the expected result."""
    return pow, (2, 3), {"mod": 5}, 3


@pytest.fixture
def failure_case():
    """GIVEN a failure WHEN a function runs THEN preserve the exception."""
    error = RuntimeError("The test function failed.")

    def raise_error():
        """GIVEN an error WHEN called THEN raise the error."""
        raise error

    return raise_error, error


@pytest.fixture
def command_case():
    """GIVEN a command WHEN it runs THEN supply its expected output."""
    script = (
        "import sys; print('output'); "
        "print('error', file=sys.stderr); sys.exit(7)"
    )
    return [sys.executable, "-c", script], (7, "output\n", "error\n")


@pytest.fixture
def directory_case(cli: CliHarness):
    """GIVEN a test project WHEN a command runs THEN use that directory."""
    script = "from pathlib import Path; print(Path.cwd())"
    return [sys.executable, "-c", script], cli.root


@pytest.fixture
def empty_case():
    """GIVEN no command WHEN execution starts THEN require a command."""
    return [], "The command must not be empty."


def test_api_arguments(api: ApiHarness, api_case):
    """GIVEN arguments WHEN the API runs THEN return its result."""
    function, args, kwargs, expected = api_case
    actual = api.call(function, *args, **kwargs)
    assert actual == expected


def test_api_exception(api: ApiHarness, failure_case):
    """GIVEN a failure WHEN the API runs THEN raise the same exception."""
    function, expected = failure_case
    with pytest.raises(RuntimeError) as caught:
        api.call(function)
    assert caught.value is expected


def test_command_result(cli: CliHarness, command_case):
    """GIVEN a command WHEN it fails THEN retain its status and output."""
    arguments, expected = command_case
    result = cli.run(arguments)
    actual = result.returncode, result.stdout, result.stderr
    assert actual == expected


def test_command_directory(cli: CliHarness, directory_case):
    """GIVEN a test project WHEN a command runs THEN use that directory."""
    arguments, expected = directory_case
    result = cli.run(arguments)
    actual = Path(result.stdout.rstrip("\n"))
    assert actual == expected


def test_empty_command(cli: CliHarness, empty_case):
    """GIVEN no command WHEN execution starts THEN raise an error."""
    arguments, expected = empty_case
    with pytest.raises(ValueError) as caught:
        cli.run(arguments)
    assert str(caught.value) == expected
