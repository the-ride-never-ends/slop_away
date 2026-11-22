"""Test fix feature scenarios."""

from pytest_bdd import scenario


@scenario("features/fix.feature", "apply_fixes applies safe fixes")
def test_fix_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/fix.feature",
    "apply_fixes does not apply unsafe fixes by default",
)
def test_fix_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/fix.feature", "apply_fixes applies unsafe fixes when asked"
)
def test_fix_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/fix.feature", "Findings with no fix remain after fixing")
def test_fix_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/fix.feature", "A second fix pass changes nothing")
def test_fix_05():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/fix.feature", "check --fix rewrites the file on disk")
def test_fix_06():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
