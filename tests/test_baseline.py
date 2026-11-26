"""Test baseline feature scenarios."""

from pathlib import Path

import pytest
from pytest_bdd import scenario

from slop_away import Config, check_text


@scenario(
    "features/baseline.feature",
    "check --write-baseline writes the baseline file",
)
def test_baseline_01():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/baseline.feature", "Findings in the baseline do not fail the run")
def test_baseline_02():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario("features/baseline.feature", "A finding not in the baseline fails the run")
def test_baseline_03():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/baseline.feature",
    "A baselined finding still matches after its lines move",
)
def test_baseline_04():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/baseline.feature",
    "Editing a baselined sentence makes its findings new",
)
def test_baseline_05():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@scenario(
    "features/baseline.feature",
    "A baselined finding still matches after its list marker changes",
)
def test_baseline_06():
    """GIVEN the feature setup WHEN the action runs THEN check its result."""


@pytest.mark.parametrize("marker", ["- ", "* ", "+ ", "1. ", "12. ", "  - "])
def test_fingerprint_ignores_list_marker(marker):
    """GIVEN a list item WHEN checked THEN hash it like the bare sentence."""
    config = Config(root=Path("."))
    bare = check_text("Never edit generated files.\n", "docs/a.md", config)
    item = check_text(f"{marker}Never edit generated files.\n", "docs/a.md", config)
    assert [f.fingerprint for f in item] == [f.fingerprint for f in bare]
