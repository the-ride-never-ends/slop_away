"""Test the markdown feature scenarios."""

from pytest_bdd import scenario


@scenario(
    "features/markdown.feature",
    "Text in a fenced code block produces no findings",
)
def test_markdown_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/markdown.feature", "Inline code produces no findings")
def test_markdown_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/markdown.feature", "Front matter produces no findings")
def test_markdown_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/markdown.feature", "A bare URL produces no findings")
def test_markdown_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/markdown.feature", "Table cells produce no prose findings")
def test_markdown_05():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/markdown.feature", "Link text is checked as prose")
def test_markdown_07():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/markdown.feature", "An HTML comment is skipped by prose rules"
)
def test_markdown_06():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
