"""Test repeated sentences across selected files."""

from pathlib import Path

import pytest

from slop_away import Config, check_files

SENTENCE = "The cache is cleared every time the tool starts a new run."


@pytest.fixture(
    params=[
        (
            {"a.md": SENTENCE, "b.md": SENTENCE},
            ["b.md", "a.md"],
            {},
            [("b.md", "VRB005", 1, 1)],
        ),
        (
            {"a.md": SENTENCE, "b.md": SENTENCE.upper()},
            ["a.md", "b.md"],
            {},
            [("b.md", "VRB005", 1, 1)],
        ),
        (
            {"a.md": SENTENCE, "b.md": SENTENCE.replace(" ", "  ")},
            ["a.md", "b.md"],
            {},
            [("b.md", "VRB005", 1, 1)],
        ),
        (
            {"a.md": SENTENCE, "b.md": SENTENCE + "\n\n" + SENTENCE},
            ["a.md", "b.md"],
            {},
            [("b.md", "VRB005", 1, 1), ("b.md", "VRB005", 3, 1)],
        ),
        ({"a.md": SENTENCE + "\n\n" + SENTENCE}, ["a.md", "a.md"], {}, []),
        (
            {"a.md": "```text\n" + SENTENCE + "\n```", "b.md": SENTENCE},
            ["a.md", "b.md"],
            {},
            [],
        ),
        (
            {"AGENTS.md": SENTENCE, "b.md": SENTENCE},
            ["AGENTS.md", "b.md"],
            {},
            [],
        ),
        (
            {"a.md": SENTENCE, "b.md": SENTENCE},
            ["a.md", "b.md"],
            {"a.md": {"ignore": ["VRB005"]}},
            [],
        ),
        (
            {"a.md": SENTENCE, "b.md": SENTENCE},
            ["a.md", "b.md"],
            {"b.md": {"ignore": ["VRB005"]}},
            [],
        ),
        (
            {"a.md": SENTENCE, "b.md": SENTENCE.replace(".", "!")},
            ["a.md", "b.md"],
            {},
            [],
        ),
    ]
)
def repeat_case(tmp_path, request):
    """GIVEN selected files WHEN checked THEN compare eligible sentences."""
    sources, paths, profiles, records = request.param
    for path, text in sources.items():
        (tmp_path / path).write_text(text, encoding="utf-8")
    config = Config(root=tmp_path, select=["VRB005"], profiles=profiles)
    expected = [
        (Path(path), code, line, column)
        for path, code, line, column in records
    ]
    return paths, config, expected


def test_file_repeats(repeat_case):
    """GIVEN selected files WHEN checked THEN report later repeats."""
    paths, config, expected = repeat_case
    findings = check_files(paths, config)
    actual = [
        (item.path, item.code, item.line, item.column) for item in findings
    ]
    assert actual == expected
