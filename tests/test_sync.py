"""Test the sync feature scenarios."""

from pytest_bdd import scenario


@scenario(
    "features/sync.feature",
    "sync downloads configured packages into the cache",
)
def test_sync_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/sync.feature",
    "check exits 2 and names a configured package that is not synced",
)
def test_sync_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/sync.feature", "check runs without network access after sync"
)
def test_sync_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
