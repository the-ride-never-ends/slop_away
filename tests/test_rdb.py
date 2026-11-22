"""Test the rdb feature scenarios."""

from pytest_bdd import scenario


@scenario(
    "features/rdb.feature", "RDB001 flags an h2 section above the grade limit"
)
def test_rdb_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/rdb.feature", "An h2 section at or below the limit passes")
def test_rdb_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/rdb.feature", "A profile changes the grade limit")
def test_rdb_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/rdb.feature",
    "Lists, tables, and code do not count toward the score",
)
def test_rdb_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
