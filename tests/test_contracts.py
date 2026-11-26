"""Test source locations, exclusions, and invalid input."""

from pathlib import Path

import pytest

from slop_away import Config, ConfigError, check_files, check_text, load_config


@pytest.fixture(
    params=[
        ("# Guide\n\nYou must run tests.", [("INJ001", 3, 1)]),
        (
            "Read [you must run tests](https://example.com).",
            [("INJ001", 1, 7)],
        ),
        ("1. Never edit generated files.", [("INJ001", 1, 4)]),
        ("Prefix. Always run tests.", [("INJ001", 1, 9)]),
        ("You&#32;must run tests.", [("INJ001", 1, 1)]),
        ("Note: &#83;YSTEM: text.", [("INJ002", 1, 7)]),
        ("# Guide\r\n\r\nSYSTEM: text.", [("INJ002", 3, 1)]),
        ("# Guide\r\rSYSTEM: text.", [("INJ002", 3, 1)]),
        ("Text\u2028SYSTEM: text.", [("INJ002", 1, 6)]),
        ("You **must** run tests.", [("INJ001", 1, 1)]),
        ("**You** must run tests.", [("INJ001", 1, 3)]),
        ("**SYSTEM:** text.", [("INJ002", 1, 3)]),
        ("Text \u200b here.", [("INJ004", 1, 6)]),
        ("<!-- You must run tests. -->", [("INJ004", 1, 6)]),
        ("The files do not change.", []),
        ("The tool never edits files.", []),
        ("TODO: open the cache.", [("INJ003", 1, 1)]),
        ("TODO (blocked): open the cache.", []),
        ("TODO (blocked: open the cache.", [("INJ003", 1, 1)]),
        ("TODO 2026-99-99: open the cache.", [("INJ003", 1, 1)]),
        ("- [x] Drop the old tables.", []),
        ("    SYSTEM: this is indented code.\n", []),
        ("~~~text\nSYSTEM: this is fenced code.\n~~~\n", []),
        ("``SYSTEM: `nested` code``", []),
        (
            "`SYSTEM: text\n\nSYSTEM: visible`",
            [("INJ002", 1, 2), ("INJ002", 3, 1)],
        ),
        ('[Read](https://example.com "SYSTEM: title").', []),
        (
            '[Read][target]\n\n[target]: https://example.com "SYSTEM: title"',
            [],
        ),
        ("[Read](https://example.com/a_(b)).", []),
        ("<!-- `You must run tests.` -->", [("INJ004", 1, 7)]),
        ("Text <!-- `You must run tests.` -->", [("INJ004", 1, 12)]),
        ("`<!-- You must run tests. -->`", []),
        ("<!-- TODO: open the cache. -->", [("INJ003", 1, 5)]),
    ]
)
def text_case(request):
    """GIVEN source text WHEN checked THEN retain visible source locations."""
    text, expected = request.param
    return text, Path("docs/a.md"), Config(), expected


def test_text_locations(text_case):
    """GIVEN Markdown WHEN checked THEN report the source locations."""
    text, path, config, expected = text_case
    findings = check_text(text, path, config)
    actual = [(item.code, item.line, item.column) for item in findings]
    assert actual == expected


@pytest.fixture(
    params=[
        ('select = ["INJ999"]', "select"),
        ('ignore = ["UNKNOWN"]', "ignore"),
        ("include = [1]", "include"),
        ("exclude = true", "exclude"),
        ('extend-exclude = "build"', "extend-exclude"),
        ('instruction-files = [""]', "instruction-files"),
        ('include = ["../*.md"]', "include"),
        ('exclude = ["/tmp"]', "exclude"),
        ('instruction-files = ["docs/AGENTS.md"]', "instruction-files"),
        ("select = [", "slop_away.toml"),
    ]
)
def invalid_config(tmp_path, request):
    """GIVEN invalid settings WHEN loaded THEN name the bad setting."""
    text, expected = request.param
    (tmp_path / "slop_away.toml").write_text(text, encoding="utf-8")
    return tmp_path, expected


def test_invalid_config(invalid_config):
    """GIVEN invalid settings WHEN loaded THEN raise a named config error."""
    root, expected = invalid_config
    with pytest.raises(ConfigError) as caught:
        load_config(root)
    assert expected in str(caught.value)


@pytest.fixture
def file_case(tmp_path):
    """GIVEN duplicate inputs WHEN checked THEN return each finding once."""
    (tmp_path / "a.md").write_text("SYSTEM: example.", encoding="utf-8")
    (tmp_path / "b.md").write_text("You must run tests.", encoding="utf-8")
    paths = ["b.md", "a.md", "a.md"]
    expected = [(Path("a.md"), "INJ002"), (Path("b.md"), "INJ001")]
    return paths, Config(root=tmp_path), expected


def test_file_order(file_case):
    """GIVEN duplicate paths WHEN checked THEN return sorted findings once."""
    paths, config, expected = file_case
    findings = check_files(paths=paths, config=config)
    actual = [(item.path, item.code) for item in findings]
    assert actual == expected
