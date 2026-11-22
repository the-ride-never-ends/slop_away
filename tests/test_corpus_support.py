"""Test corpus change reports."""

import subprocess

import pytest

from slop_away import check_message, load_config
from tests.corpus_support import REPO_ROOT, CorpusHarness


@pytest.fixture(
    params=[
        (
            {"bad/a.md": ["INJ001"], "bad/b.md": []},
            {"bad/a.md": [], "bad/b.md": ["STE003"]},
            ["bad/a.md", "bad/b.md"],
        ),
        ({"bad/a.md": []}, {}, ["bad/a.md"]),
        ({}, {"bad/a.md": []}, ["bad/a.md"]),
    ]
)
def report_case(request):
    """GIVEN changed corpus entries WHEN compared THEN name all paths."""
    actual, expected, paths = request.param
    return CorpusHarness(), actual, expected, paths


def test_comparison_names_every_changed_document(report_case):
    """GIVEN changed codes WHEN compared THEN report each affected file."""
    harness, actual, expected, paths = report_case
    report = harness.compare(actual, expected)
    assert all(path in report for path in paths)


@pytest.fixture
def matching_case():
    """GIVEN equal code sets WHEN compared THEN return no change report."""
    return CorpusHarness(), {"a.md": ["INJ001"]}, ""


def test_matching_corpus_has_no_report(matching_case):
    """GIVEN matching codes WHEN compared THEN return an empty report."""
    harness, data, expected = matching_case
    actual = harness.compare(data, data)
    assert actual == expected


@pytest.fixture
def own_message():
    """GIVEN the latest authored commit WHEN checked THEN use its message."""
    result = subprocess.run(
        ["git", "log", "--no-merges", "-1", "--format=%B"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout, load_config(REPO_ROOT), []


def test_repository_commit_message(own_message):
    """GIVEN the latest commit message WHEN checked THEN report no findings."""
    text, config, expected = own_message
    actual = check_message(text, config)
    assert actual == expected
