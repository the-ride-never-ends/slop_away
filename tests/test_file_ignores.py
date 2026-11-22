"""Test per-file rule ignores."""

import pytest

from slop_away import (
    Config,
    ConfigError,
    PackageError,
    apply_fixes,
    check_text,
    sync_packages,
)
from tests.package_steps import DELVE


@pytest.fixture(
    params=[
        ({"docs/**/*.md": ["INJ001"]}, {}, "docs/a.md", []),
        ({"docs/**/*.md": ["INJ"]}, {}, "docs/deep/a.md", []),
        ({"docs/*.md": ["INJ001"]}, {}, "docs/deep/a.md", ["INJ001"]),
        ({"docs/*.md": ["INJ001"]}, {}, "a.md", ["INJ001"]),
        (
            {"docs/*.md": ["INJ001"], "**/*.md": ["INJ002"]},
            {},
            "docs/a.md",
            [],
        ),
        (
            {"docs/*.md": ["INJ001"]},
            {"docs/*.md": {"ignore": []}},
            "docs/a.md",
            [],
        ),
        ({"docs/*.md": []}, {}, "docs/a.md", ["INJ001"]),
    ]
)
def ignore_case(request, tmp_path):
    """GIVEN matching globs WHEN checked THEN combine all file ignores."""
    ignored, profiles, path, expected = request.param
    config = Config(
        root=tmp_path,
        select=["INJ001"],
        per_file_ignores=ignored,
        profiles=profiles,
    )
    return config, path, expected


def test_per_file_rule_selection(ignore_case):
    """GIVEN per-file ignores WHEN checked THEN remove matching rules."""
    config, path, expected = ignore_case
    findings = check_text("You must run the tool.", path, config)
    assert [finding.code for finding in findings] == expected


@pytest.fixture(
    params=[
        [],
        "INJ",
        {"a.md": "INJ"},
        {1: ["INJ"]},
        {"../a.md": ["INJ"]},
        {"/a.md": ["INJ"]},
        {"": ["INJ"]},
        {"a.md": ["missing"]},
        {"a.md": [1]},
    ]
)
def invalid_ignores(request):
    """GIVEN invalid ignore settings WHEN configured THEN reject them."""
    return request.param, "per-file-ignores"


def test_invalid_per_file_ignores(invalid_ignores):
    """GIVEN invalid ignores WHEN configured THEN name the setting."""
    value, expected = invalid_ignores
    with pytest.raises(ConfigError) as error:
        Config(per_file_ignores=value)
    assert expected in str(error.value)


@pytest.fixture
def ignored_fix(tmp_path):
    """GIVEN ignored fix rules WHEN fixing THEN preserve their text."""
    text = "In order to run the tool, open a shell."
    config = Config(root=tmp_path, per_file_ignores={"docs/*.md": ["VRB001"]})
    return text, config


def test_ignores_control_fixes(ignored_fix):
    """GIVEN a per-file ignore WHEN fixing THEN keep its original text."""
    expected, config = ignored_fix
    actual = apply_fixes(expected, "docs/a.md", config, True)
    assert actual == expected


@pytest.fixture(params=["test-pkg", "test-pkg.Delve"])
def ignored_package(request, tmp_path, package_server):
    """GIVEN package ignores WHEN checking THEN skip matching rules."""
    package_server.store("test-pkg", {"test-pkg/Delve.yml": DELVE})
    config = Config(
        root=tmp_path,
        packages=[package_server.url("test-pkg")],
        select=["test-pkg"],
        per_file_ignores={"docs/*.md": [request.param]},
    )
    sync_packages(config)
    return config, []


def test_per_file_package_ignores(ignored_package):
    """GIVEN an external ignore WHEN checked THEN omit its findings."""
    config, expected = ignored_package
    actual = check_text("We delve into the parser.", "docs/a.md", config)
    assert actual == expected


@pytest.fixture
def unknown_ignored_rule(tmp_path, package_server):
    """GIVEN a missing external rule WHEN checking THEN fail fast."""
    package_server.store("test-pkg", {"test-pkg/Delve.yml": DELVE})
    config = Config(
        root=tmp_path,
        packages=[package_server.url("test-pkg")],
        per_file_ignores={"never/*.md": ["test-pkg.Missing"]},
    )
    sync_packages(config)
    return config, "test-pkg.Missing"


def test_unknown_per_file_package_rule(unknown_ignored_rule):
    """GIVEN an unknown ignored rule WHEN checked THEN reject its name."""
    config, expected = unknown_ignored_rule
    with pytest.raises(PackageError) as error:
        check_text("The tool runs.", "a.md", config)
    assert expected in str(error.value)
