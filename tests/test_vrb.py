"""Test the vrb feature scenarios."""

from pytest_bdd import scenario


@scenario("features/vrb.feature", "VRB001 flags a filler phrase")
def test_vrb_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/vrb.feature", "VRB002 flags a hedge phrase")
def test_vrb_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/vrb.feature", "VRB003 flags a file over its glob's word budget"
)
def test_vrb_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/vrb.feature",
    "VRB004 flags a sentence repeated within one document",
)
def test_vrb_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/vrb.feature", "VRB005 flags a sentence repeated across documents"
)
def test_vrb_05():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/vrb.feature", "A repeated sentence under 8 words passes")
def test_vrb_06():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""
