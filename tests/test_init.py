"""Test init feature scenarios."""

from pytest_bdd import scenario


@scenario("features/init.feature", "init writes every part by default")
def test_init_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/init.feature", "Each skip flag leaves out its part")
def test_init_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/init.feature",
    "An existing slop_away.toml stops init before it writes anything",
)
def test_init_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/init.feature", "init does not write CODEOWNERS")
def test_init_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/init.feature",
    "init adds its hooks to an existing pre-commit config",
)
def test_init_05():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/init.feature",
    "init adds its hook entries to an existing Claude Code settings file",
)
def test_init_06():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/init.feature",
    "init adds the cache folder to an existing .gitignore",
)
def test_init_07():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
