"""Test the config feature scenarios."""

from pytest_bdd import scenario


@scenario(
    "features/config.feature",
    "Settings are read from the tool.slop_away section of pyproject.toml",
)
def test_config_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/config.feature", "Settings are read from slop_away.toml")
def test_config_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/config.feature",
    "slop_away.toml takes precedence over pyproject.toml",
)
def test_config_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/config.feature", "An unknown key raises ConfigError")
def test_config_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/config.feature", "An invalid value raises ConfigError")
def test_config_05():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/config.feature", "select limits the run to the listed rules"
)
def test_config_06():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/config.feature", "ignore removes the listed rules")
def test_config_07():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/config.feature",
    "A pyproject.toml without a tool.slop_away section is ignored",
)
def test_config_11():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/config.feature",
    "A profile changes rule settings for files matching its glob",
)
def test_config_08():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/config.feature",
    "per-file-ignores removes rules for matching files",
)
def test_config_09():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/config.feature", "An inline suppression comment has no effect"
)
def test_config_10():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
