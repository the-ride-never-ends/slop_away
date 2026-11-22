"""Test baseline feature scenarios."""

from pytest_bdd import scenario


@scenario(
    "features/baseline.feature",
    "check --write-baseline writes the baseline file",
)
def test_baseline_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/baseline.feature", "Findings in the baseline do not fail the run"
)
def test_baseline_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/baseline.feature", "A finding not in the baseline fails the run"
)
def test_baseline_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/baseline.feature",
    "A baselined finding still matches after its lines move",
)
def test_baseline_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/baseline.feature",
    "Editing a baselined sentence makes its findings new",
)
def test_baseline_05():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
