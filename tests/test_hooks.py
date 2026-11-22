"""Test hooks feature scenarios."""

from pytest_bdd import scenario


@scenario(
    "features/hooks.feature",
    "The post-edit hook reports findings in an edited Markdown file",
)
def test_hooks_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/hooks.feature", "The post-edit hook passes a clean file")
def test_hooks_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/hooks.feature",
    "The post-edit hook ignores files that are not Markdown",
)
def test_hooks_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/hooks.feature", "The stop hook blocks while findings remain"
)
def test_hooks_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/hooks.feature",
    "The stop hook allows stopping on the second pass",
)
def test_hooks_05():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/hooks.feature",
    "The pre-bash hook blocks commits that skip hooks",
)
def test_hooks_06():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/hooks.feature", "The pre-bash hook allows a normal commit")
def test_hooks_07():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
