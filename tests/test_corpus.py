"""Test corpus feature scenarios."""

from pytest_bdd import scenario


@scenario(
    "features/corpus.feature",
    "Each bad document produces exactly its expected codes",
)
def test_corpus_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/corpus.feature", "Each fixed document produces no findings"
)
def test_corpus_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/corpus.feature", "Each good document produces no findings")
def test_corpus_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/corpus.feature",
    "A change in findings names each affected document",
)
def test_corpus_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/corpus.feature",
    "The slop_away repository's own docs produce no findings",
)
def test_corpus_05():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
