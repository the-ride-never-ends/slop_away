"""Test the selection feature scenarios."""

from pytest_bdd import scenario


@scenario(
    "features/selection.feature", "A recursive glob selects nested files"
)
def test_selection_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/selection.feature",
    "A directory path selects the Markdown files under it",
)
def test_selection_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/selection.feature", "exclude removes matching files")
def test_selection_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/selection.feature", "extend-exclude adds to the default excludes"
)
def test_selection_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/selection.feature", "Files listed in .gitignore are skipped"
)
def test_selection_05():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/selection.feature", "Files that are not Markdown are skipped"
)
def test_selection_06():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/selection.feature",
    "A file named directly is selected when a setting skips it",
)
def test_selection_07():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/selection.feature",
    "force_exclude skips a file named directly",
)
def test_selection_08():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/selection.feature",
    "A directory input still follows the excludes",
)
def test_selection_09():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
