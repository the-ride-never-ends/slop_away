"""Test project terminology through document checks."""

import pytest

from slop_away import Config, ConfigError, check_text, load_config


@pytest.fixture(
    params=[
        ("Open the folder.", {"directory": ["folder"]}, [("STE007", 1, 10)]),
        ("Open the FOLDER.", {"directory": ["folder"]}, [("STE007", 1, 10)]),
        (
            "Open the **folder**.",
            {"directory": ["folder"]},
            [("STE007", 1, 12)],
        ),
        (
            "Open the fo&#108;der.",
            {"directory": ["folder"]},
            [("STE007", 1, 10)],
        ),
        (
            "Open [folder](https://example.com).",
            {"directory": ["folder"]},
            [("STE007", 1, 7)],
        ),
        (
            "Open [folder][term].\n\n[term]: https://example.com",
            {"directory": ["folder"], "label": ["term"]},
            [("STE007", 1, 7)],
        ),
        (
            "Open [folder][term].",
            {"directory": ["folder"], "label": ["term"]},
            [("STE007", 1, 7), ("STE007", 1, 15)],
        ),
        ("Open the folderful example.", {"directory": ["folder"]}, []),
        ("Open the folders.", {"directory": ["folder"]}, []),
        (
            "Open the folder's file.",
            {"directory": ["folder"]},
            [("STE007", 1, 10)],
        ),
        (
            "Use the power\nunit.",
            {"power supply": ["power unit"]},
            [("STE007", 1, 9)],
        ),
        (
            "Use **power** unit.",
            {"power supply": ["power unit"]},
            [("STE007", 1, 7)],
        ),
        ("Use CPP.", {"C++": ["CPP"]}, [("STE007", 1, 5)]),
        ("Open `folder`.", {"directory": ["folder"]}, []),
        ("<!-- Open the folder. -->", {"directory": ["folder"]}, []),
        ("See https://example.com/folder.", {"directory": ["folder"]}, []),
        ("---\nname: folder\n---", {"directory": ["folder"]}, []),
        ("| Term |\n| --- |\n| folder |", {"directory": ["folder"]}, []),
    ]
)
def glossary_case(request):
    """GIVEN banned terms WHEN checked THEN locate complete term matches."""
    text, glossary, expected = request.param
    return text, Config(select=["STE007"], glossary=glossary), expected


def test_glossary_terms(glossary_case):
    """GIVEN a glossary WHEN checked THEN locate the banned terms."""
    text, config, expected = glossary_case
    findings = check_text(text, "docs/a.md", config)
    actual = [(item.code, item.line, item.column) for item in findings]
    assert actual == expected


@pytest.fixture
def glossary_hint():
    """GIVEN a banned term WHEN checked THEN name the preferred term."""
    config = Config(select=["STE007"], glossary={"directory": ["folder"]})
    return "Open the folder.", config, ["Use 'directory' instead of 'folder'."]


def test_glossary_hint(glossary_hint):
    """GIVEN a banned term WHEN checked THEN give its replacement hint."""
    text, config, expected = glossary_hint
    findings = check_text(text, "docs/a.md", config)
    actual = [finding.hint for finding in findings]
    assert actual == expected


@pytest.fixture(
    params=[
        "glossary = []",
        '[glossary]\n"" = ["folder"]',
        '[glossary]\ndirectory = "folder"',
        "[glossary]\ndirectory = [1]",
        '[glossary]\ndirectory = [""]',
        '[glossary]\ndirectory = ["directory"]',
        '[glossary]\ndirectory = ["folder"]\nfolder = []',
        '[glossary]\ndirectory = ["folder"]\npath = ["FOLDER"]',
        "[glossary]\nDirectory = []\ndirectory = []",
        '[glossary]\n" directory " = ["folder"]',
        '[glossary]\ndirectory = [" folder "]',
        '[glossary]\ndirectory = ["foo\\nbar"]',
        '[profiles."docs/*.md"]\nglossary = {directory = ["folder"]}',
    ]
)
def invalid_glossary(tmp_path, request):
    """GIVEN invalid terminology WHEN loaded THEN report a config error."""
    (tmp_path / "slop_away.toml").write_text(request.param, encoding="utf-8")
    return tmp_path, "glossary"


def test_glossary_errors(invalid_glossary):
    """GIVEN invalid terminology WHEN loaded THEN name the glossary."""
    root, expected = invalid_glossary
    with pytest.raises(ConfigError) as caught:
        load_config(root)
    assert expected in str(caught.value)
