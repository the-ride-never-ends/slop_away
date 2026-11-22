"""Test the STE feature scenarios."""

from pytest_bdd import scenario


@scenario(
    "features/ste.feature", "STE001 flags a procedure sentence over 20 words"
)
def test_ste_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/ste.feature",
    "STE001 passes a description sentence of 21 to 25 words",
)
def test_ste_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/ste.feature", "STE001 flags a description sentence over 25 words"
)
def test_ste_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/ste.feature", "STE002 flags a paragraph over 6 sentences")
def test_ste_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/ste.feature", "STE003 flags a passive sentence")
def test_ste_05():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/ste.feature", "STE004 flags a contraction")
def test_ste_06():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/ste.feature", "STE005 flags a sentence not in a simple tense"
)
def test_ste_07():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/ste.feature", "STE006 flags a noun cluster over 3 nouns")
def test_ste_08():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/ste.feature", "STE007 flags a banned synonym from the glossary"
)
def test_ste_09():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
