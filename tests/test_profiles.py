"""Test profile limits and validation through the public API."""

import pytest

from slop_away import Config, ConfigError, check_text, load_config


@pytest.fixture(
    params=[
        (
            {
                "ignore": ["VRB001"],
                "profiles": {"docs/**/*.md": {"ignore": []}},
            },
            "docs/a.md",
            ["VRB001", "INJ001"],
        ),
        (
            {
                "select": ["INJ"],
                "profiles": {"docs/**/*.md": {"select": ["VRB"]}},
            },
            "docs/a.md",
            ["VRB001"],
        ),
        (
            {"profiles": {"docs/**/*.md": {"ignore": ["VRB001"]}}},
            "docs/a.md",
            ["INJ001"],
        ),
        (
            {
                "profiles": {
                    "docs/**/*.md": {"ignore": ["VRB001"]},
                    "docs/a.md": {"ignore": []},
                }
            },
            "docs/a.md",
            ["VRB001", "INJ001"],
        ),
        (
            {"profiles": {"docs/*.md": {"ignore": ["VRB001"]}}},
            "docs/sub/a.md",
            ["VRB001", "INJ001"],
        ),
        (
            {
                "select": ["VRB003"],
                "word_budget": 2,
                "profiles": {"docs/**/*.md": {"word-budget": 100}},
            },
            "other/a.md",
            ["VRB003"],
        ),
    ]
)
def profile_case(request):
    """GIVEN file profiles WHEN checked THEN apply matching settings."""
    settings, path, expected = request.param
    text = "It is worth noting that the tool runs. You must run tests."
    return text, path, Config(**settings), expected


def test_profile_rules(profile_case):
    """GIVEN profiles WHEN checked THEN use their final rule settings."""
    text, path, config, expected = profile_case
    findings = check_text(text, path, config)
    actual = [finding.code for finding in findings]
    assert actual == expected


@pytest.fixture(
    params=[
        ("max-grade = true", "max-grade"),
        ("max-grade = -1", "max-grade"),
        ("max-grade = nan", "max-grade"),
        ("max-grade = inf", "max-grade"),
        ("word-budget = false", "word-budget"),
        ("word-budget = 1.5", "word-budget"),
        ("word-budget = -1", "word-budget"),
        ("profiles = []", "profiles"),
        ('[profiles.".git/*"]\ncommit-body-budget = 0', "commit-body-budget"),
        ('[profiles."docs/*.md"]\nunknown = 1', "unknown"),
        ('[profiles."docs/*.md"]\nword-budget = true', "word-budget"),
        ('[profiles."docs/*.md"]\nmax-grade = nan', "max-grade"),
        ('[profiles."docs/*.md"]\nselect = ["WRONG"]', "select"),
        ('[profiles."../*.md"]\nmax-grade = 10', "profiles"),
        ('[profiles." "]\nmax-grade = 10', "profiles"),
        ('[profiles]\n"docs/*.md" = []', "docs/*.md"),
    ]
)
def invalid_profile(tmp_path, request):
    """GIVEN invalid profile settings WHEN loaded THEN name the bad key."""
    text, expected = request.param
    (tmp_path / "slop_away.toml").write_text(text, encoding="utf-8")
    return tmp_path, expected


def test_profile_errors(invalid_profile):
    """GIVEN invalid profiles WHEN loaded THEN raise a named config error."""
    root, expected = invalid_profile
    with pytest.raises(ConfigError) as caught:
        load_config(root)
    assert expected in str(caught.value)
