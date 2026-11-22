"""Test the precommit feature scenarios."""

from pytest_bdd import scenario


@scenario(
    "features/precommit.feature",
    "The slop_away hook blocks a commit with findings",
)
def test_precommit_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/precommit.feature", "The slop_away hook allows a clean commit"
)
def test_precommit_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/precommit.feature",
    "The slop_away-sync hook syncs configured packages",
)
def test_precommit_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/precommit.feature",
    "The slop_away-msg hook blocks a commit message with findings",
)
def test_precommit_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
