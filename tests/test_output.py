"""Test the output feature scenarios."""

from pytest_bdd import scenario


@scenario(
    "features/output.feature",
    "The text format shows path, line, column, code, and message",
)
def test_output_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/output.feature",
    "The agent format prints one line per finding with a fix hint",
)
def test_output_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/output.feature", "Nothing but findings is printed")
def test_output_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/output.feature",
    "The json format prints a JSON array of findings",
)
def test_output_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/output.feature",
    "The github format prints GitHub Actions annotations",
)
def test_output_05():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
