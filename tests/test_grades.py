"""Test readability boundaries through document checks."""

import pytest

from slop_away import Config, check_text

COMPLEX = (
    "The implementation of comprehensive configuration management "
    "necessitates considerable organizational coordination across numerous "
    "interdependent infrastructure components."
)


@pytest.fixture(
    params=[
        ("## Easy\n\nThe cat sat on the mat.", 0, []),
        ("## Words\n\n" + "cat " * 35 + ".", 9.86, []),
        ("## Words\n\n" + "cat " * 35 + ".", 9.85, [("RDB001", 1, 1)]),
        ("## Words\n\n" + "cat " * 35 + ".", 9.85999, [("RDB001", 1, 1)]),
        ("## Words\n\n" + "cat " * 35 + ".\n\n123.", 9, [("RDB001", 1, 1)]),
        (COMPLEX, 0, []),
        (COMPLEX + "\n\n## Easy\n\nThe cat sat on the mat.", 0, []),
        ("## Easy\n\nThe cat sat on the mat.\n\n# Next\n\n" + COMPLEX, 0, []),
        ("## Topic\n\n### Detail\n\n" + COMPLEX, 10, [("RDB001", 1, 1)]),
        (
            "## Difficult\n\n" + COMPLEX + "\n\n## Easy\n\nThe cat sat.",
            10,
            [("RDB001", 1, 1)],
        ),
        ("## Empty", 0, []),
        ("## Lists\n\n1. " + COMPLEX, 0, []),
        ("## Lists\n\n- Item\n\n    " + COMPLEX, 0, []),
        ("## Topic\n\n- ## Nested\n\n" + COMPLEX, 10, [("RDB001", 1, 1)]),
        ("## Topic\n\n```text\n" + COMPLEX + "\n```", 0, []),
        ("## Topic\n\n<!-- " + COMPLEX + " -->", 0, []),
        (
            (
                "## Topic\n\n"
                "The red cat sat on the mat by https://example.com. "
                "The red cat sat on the mat by https://other.com."
            ),
            0,
            [],
        ),
        ("## Topic\n\n123.\n\n456.", 0, []),
    ]
)
def grade_case(request):
    """GIVEN a section and limit WHEN checked THEN compare its grade."""
    text, limit, expected = request.param
    return text, Config(select=["RDB"], max_grade=limit), expected


def test_section_grades(grade_case):
    """GIVEN h2 sections WHEN checked THEN flag only grades above the limit."""
    text, config, expected = grade_case
    findings = check_text(text, "docs/a.md", config)
    actual = [(item.code, item.line, item.column) for item in findings]
    assert actual == expected
