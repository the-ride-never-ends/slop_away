"""Test the ait feature scenarios."""

from pytest_bdd import scenario


@scenario(
    "features/ait.feature", "An existence rule flags its token at its position"
)
def test_ait_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/ait.feature", "A substitution rule names the replacement")
def test_ait_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/ait.feature", "An occurrence rule flags a count over its limit"
)
def test_ait_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/ait.feature", "A sequence rule flags its part-of-speech pattern"
)
def test_ait_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/ait.feature", "External findings use the package's rule name"
)
def test_ait_05():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/ait.feature",
    "A synced package that the config does not list does not run",
)
def test_ait_06():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/ait.feature",
    "An explicit select that leaves out the package excludes its rules",
)
def test_ait_07():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/ait.feature",
    "ignore removes package rules by package name or rule code",
)
def test_ait_08():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
