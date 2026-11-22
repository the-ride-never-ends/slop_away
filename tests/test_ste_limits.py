"""Test STE sentence and paragraph limits."""

import pytest

from slop_away import Config, check_text


@pytest.fixture(
    params=[
        ("Open the file " + "now " * 17 + ".", []),
        ("Open the file " + "now " * 18 + ".", ["STE001"]),
        ("The file is " + "red " * 22 + ".", []),
        ("The file is " + "red " * 23 + ".", ["STE001"]),
        ("1. The file is " + "red " * 18 + ".", ["STE001"]),
        ("- The file is " + "red " * 18 + ".", []),
        ("- Open the file " + "now " * 18 + ".", ["STE001"]),
        ("Do not change the file " + "now " * 16 + ".", ["STE001"]),
        (
            "Open the file that the parser reads " + "now " * 14 + ".",
            ["STE001"],
        ),
        ("Open the long-term file " + "now " * 16 + ".", []),
        ("Open the file if it's ready " + "now " * 14 + ".", []),
        ("Open the file " + "now " * 17 + " `many more code words`.", []),
        (
            "Open the [file][reference-id] "
            + "now " * 17
            + ".\n\n[reference-id]: https://example.com",
            [],
        ),
        (
            "Open the [file][an extra name] " + "now " * 17 + ".",
            ["STE001"],
        ),
        ("## The file is " + "red " * 23 + ".", ["STE001"]),
    ]
)
def sentence_case(request):
    """GIVEN a sentence WHEN checked THEN use its writing limit."""
    text, expected = request.param
    return text, Config(select=["STE001"]), expected


def test_sentence_limits(sentence_case):
    """GIVEN a sentence WHEN checked THEN flag only an exceeded limit."""
    text, config, expected = sentence_case
    findings = check_text(text, "docs/a.md", config)
    actual = [finding.code for finding in findings]
    assert actual == expected


@pytest.fixture(
    params=[
        ("The tool reads files. " * 6, []),
        ("The tool reads files. " * 7, ["STE002"]),
        ("The tool reads files. " * 4 + "\n\n" + "The tool runs. " * 4, []),
        ("1. " + "The tool reads files. " * 7, ["STE002"]),
        ("# " + "The tool reads files. " * 7, []),
        ("<!-- " + "The tool reads files. " * 7 + " -->", []),
        ("```text\n" + "The tool reads files. " * 7 + "\n```", []),
    ]
)
def paragraph_case(request):
    """GIVEN a paragraph WHEN checked THEN use its sentence limit."""
    text, expected = request.param
    return text, Config(select=["STE002"]), expected


def test_paragraph_limits(paragraph_case):
    """GIVEN paragraphs WHEN checked THEN flag only more than six sentences."""
    text, config, expected = paragraph_case
    findings = check_text(text, "docs/a.md", config)
    actual = [finding.code for finding in findings]
    assert actual == expected
