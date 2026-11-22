"""Test STE grammar through document checks."""

import pytest

from slop_away import Config, check_text


@pytest.fixture(
    params=[
        ("The parser reads the file.", []),
        ("The parser read the file.", []),
        ("The parser will read the file.", []),
        ("The parser can read the file.", []),
        ("The parser has a cache.", []),
        ("Reading the file takes time.", []),
        ("The file is ready.", []),
        ("The file is read by the parser.", ["STE003"]),
        ("The file was read.", ["STE003"]),
        ("The file will be read.", ["STE003"]),
        ("The file is being read.", ["STE003", "STE005"]),
        ("The file has been read.", ["STE003", "STE005"]),
        ("The parser is reading the file.", ["STE005"]),
        ("The parser was reading the file.", ["STE005"]),
        ("The parser will be reading the file.", ["STE005"]),
        ("The parser has read the file.", ["STE005"]),
        ("The parser had read the file.", ["STE005"]),
        ("The parser has been reading the file.", ["STE005"]),
        ("The file being read is large.", ["STE003"]),
        ("The parser's file is short.", []),
        ("The parser's reading the file.", ["STE004", "STE005"]),
        ("It's a short file.", ["STE004"]),
        ("The parser isn’t ready.", ["STE004"]),
        ("The parser can't stop.", ["STE004"]),
        ("The cache won't clear.", ["STE004"]),
        ("We’re ready.", ["STE004"]),
        ("They've read the file.", ["STE004", "STE005"]),
        ("Let's read the file.", ["STE004"]),
        ("The configuration file parser reads input.", []),
        ("The configuration file parser error message appears.", ["STE006"]),
        ("The configuration file\nparser error message appears.", ["STE006"]),
        ("The **configuration** file parser error appears.", ["STE006"]),
        ("The configuration file, parser error message appears.", []),
        ("The large file parser error appears.", []),
    ]
)
def grammar_case(request):
    """GIVEN prose WHEN checked THEN report the grammar rule codes."""
    text, expected = request.param
    return (
        text,
        Config(select=["STE003", "STE004", "STE005", "STE006"]),
        expected,
    )


def test_ste_grammar(grammar_case):
    """GIVEN prose WHEN checked THEN report only the expected grammar rules."""
    text, config, expected = grammar_case
    findings = check_text(text, "docs/a.md", config)
    actual = [finding.code for finding in findings]
    assert actual == expected


@pytest.fixture(
    params=[
        ("# Guide\n\nThe file is read by the parser.", [("STE003", 3, 13)]),
        ("The tool doesn’t run twice.", [("STE004", 1, 10)]),
        ("**The tool doesn't run twice.**", [("STE004", 1, 12)]),
        ("The parser is reading the file.", [("STE005", 1, 15)]),
        (
            "The configuration file parser error message appears.",
            [("STE006", 1, 5)],
        ),
        ("The parser's file is short.", []),
        ("`The parser doesn't run twice.`", []),
        ("<!-- The parser doesn't run twice. -->", []),
    ]
)
def grammar_location(request):
    """GIVEN annotated prose WHEN checked THEN preserve source locations."""
    text, expected = request.param
    return (
        text,
        Config(select=["STE003", "STE004", "STE005", "STE006"]),
        expected,
    )


def test_grammar_locations(grammar_location):
    """GIVEN prose WHEN checked THEN locate each grammar finding."""
    text, config, expected = grammar_location
    findings = check_text(text, "docs/a.md", config)
    actual = [(item.code, item.line, item.column) for item in findings]
    assert actual == expected
