"""Test commit-message feature scenarios."""

from pytest_bdd import scenario


@scenario("features/msg.feature", "MSG001 flags a subject over 72 characters")
def test_msg_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/msg.feature", "MSG002 flags a subject not in imperative mood"
)
def test_msg_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/msg.feature", "MSG003 flags a subject with a trailing period"
)
def test_msg_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/msg.feature", "MSG004 flags a body over its word budget")
def test_msg_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/msg.feature", "Trailers are skipped")
def test_msg_05():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/msg.feature", "INJ001 does not apply to commit messages")
def test_msg_06():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
