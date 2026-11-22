"""Test the inj feature scenarios."""

from pytest_bdd import scenario


@scenario(
    "features/inj.feature", "INJ001 flags a directive addressed to the reader"
)
def test_inj_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/inj.feature", "INJ001 does not apply to agent instruction files"
)
def test_inj_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/inj.feature", "INJ002 flags a role marker")
def test_inj_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/inj.feature",
    "INJ003 flags an action item without a status or date",
)
def test_inj_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/inj.feature",
    "INJ003 passes an action item with a status or date",
)
def test_inj_05():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/inj.feature", "INJ004 flags a directive inside an HTML comment"
)
def test_inj_06():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/inj.feature", "INJ004 flags invisible characters")
def test_inj_07():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/inj.feature", "INJ002 to INJ004 apply to agent instruction files"
)
def test_inj_08():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
