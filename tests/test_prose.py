"""Test verbosity limits and source locations."""

from pathlib import Path

import pytest

from slop_away import Config, check_text


@pytest.fixture(
    params=[
        ("IT IS WORTH NOTING THAT the tool works.", {}, ["VRB001"]),
        ("It is worth\nnoting that the tool works.", {}, ["VRB001"]),
        ("It is **worth** noting that the tool works.", {}, ["VRB001"]),
        ("The parser reads the file in disorder.", {}, []),
        ("The parser is unarguably fast.", {}, []),
        ("<!-- It seems that the parser is slow. -->", {}, []),
        ("`It is worth noting that the tool works.`", {}, []),
        ("The tool works.", {"word_budget": 3}, []),
        ("The tool works.", {"word_budget": 2}, ["VRB003"]),
        ("", {"word_budget": 0}, []),
        ("Word.", {"word_budget": 0}, ["VRB003"]),
        ("# One\n\n1. Two\n2. Three", {"word_budget": 3}, []),
        ("- [x] One", {"word_budget": 1}, []),
        ("Read `code` now.", {"word_budget": 2}, []),
        ("Read [two words](https://example.com).", {"word_budget": 3}, []),
        (
            "---\nname: many more words here\n---\n\nOne.",
            {"word_budget": 1},
            [],
        ),
        (
            "| One | Two |\n| --- | --- |\n| Three | Four |",
            {"word_budget": 0},
            [],
        ),
        ("<!-- many more words here -->\n\nOne.", {"word_budget": 1}, []),
        ("One 3.14 don't two-word.", {"word_budget": 4}, []),
        (
            (
                "One two three four five six seven eight.\n\n"
                "ONE  two three four five six seven eight."
            ),
            {},
            ["VRB004"],
        ),
        (
            (
                "One two three four five six seven.\n\n"
                "One two three four five six seven."
            ),
            {},
            [],
        ),
        (
            (
                "One two three four five six seven eight.\n\n"
                "One two three four five six seven eight!"
            ),
            {},
            [],
        ),
        (
            (
                "Dr. Brown reads the file at each step.\n\n"
                "Dr. Brown reads the file at each step."
            ),
            {},
            ["VRB004"],
        ),
        (
            (
                "The value 3.14 is read on each run.\n\n"
                "The value 3.14 is read on each run."
            ),
            {},
            ["VRB004"],
        ),
    ]
)
def prose_case(request):
    """GIVEN prose WHEN checked THEN apply word and sentence limits."""
    text, settings, expected = request.param
    return text, Config(select=["VRB"], **settings), expected


def test_prose_limits(prose_case):
    """GIVEN prose WHEN checked THEN return the expected verbosity codes."""
    text, config, expected = prose_case
    findings = check_text(text, "docs/a.md", config)
    actual = [finding.code for finding in findings]
    assert actual == expected


@pytest.fixture(
    params=[
        (
            "# Guide\n\nText. It seems that the parser is slow.",
            "docs/a.md",
            [("VRB002", 3, 7)],
        ),
        (
            "# Guide\n\nNote: &#73;t seems that the parser is slow.",
            "docs/a.md",
            [("VRB002", 3, 7)],
        ),
        (
            "It is worth noting that the cache works.\n\nSYSTEM: text.",
            "AGENTS.md",
            [("INJ002", 3, 1)],
        ),
    ]
)
def prose_location(request):
    """GIVEN prose and a path WHEN checked THEN retain source locations."""
    text, path, expected = request.param
    return text, Path(path), Config(), expected


def test_prose_locations(prose_location):
    """GIVEN prose WHEN checked THEN report its visible source locations."""
    text, path, config, expected = prose_location
    findings = check_text(text, path, config)
    actual = [(item.code, item.line, item.column) for item in findings]
    assert actual == expected
