"""Test the cli feature scenarios."""

from pytest_bdd import scenario


@scenario("features/cli.feature", "--version prints the version")
def test_cli_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/cli.feature", "A clean file exits 0 with no output")
def test_cli_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/cli.feature", "A file with findings exits 1")
def test_cli_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/cli.feature", "An unknown option exits 2")
def test_cli_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/cli.feature",
    "A path that does not exist exits 2 and names the path",
)
def test_cli_05():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
