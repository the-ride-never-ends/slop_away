"""Supply corpus feature steps."""

import json

import pytest
from pytest_bdd import given, parsers, then, when

from tests.corpus_support import CORPUS_ROOT, REPO_ROOT, CorpusHarness
from tests.harnesses import CliHarness


@pytest.fixture
def corpus():
    """GIVEN corpus data WHEN checked THEN use the repository corpus."""
    return CorpusHarness()


@given(
    parsers.parse("the {group} documents in the corpus"),
    target_fixture="corpus_group",
)
def corpus_group(group):
    """GIVEN a corpus group WHEN checked THEN use that group."""
    return group


@when("check_files runs on each document", target_fixture="corpus_codes")
def check_corpus(corpus, corpus_group):
    """GIVEN a corpus group WHEN checked THEN retain each file's codes."""
    return corpus.check(corpus_group)


@then("each document's codes equal its expected codes")
def expected_codes(corpus, corpus_codes):
    """GIVEN bad corpus files WHEN checked THEN match all expected codes."""
    expected = json.loads((CORPUS_ROOT / "expected.json").read_text())
    report = corpus.compare(corpus_codes, expected)
    assert not report, report


@then("each document has no findings")
def clean_corpus(corpus_codes):
    """GIVEN clean corpus files WHEN checked THEN report no codes."""
    actual = {path: codes for path, codes in corpus_codes.items() if codes}
    expected = {}
    assert actual == expected


@given(
    "a bad document whose expected codes leave out a code it produces",
    target_fixture="comparison_case",
)
def changed_corpus(tmp_path):
    """GIVEN a changed code set WHEN compared THEN retain its path."""
    directory = tmp_path / "bad"
    directory.mkdir()
    (directory / "changed.md").write_text("You must run the tests first.")
    harness = CorpusHarness(tmp_path)
    return (
        harness,
        harness.check("bad"),
        {"bad/changed.md": []},
        "bad/changed.md",
    )


@when("the corpus comparison runs", target_fixture="comparison_report")
def compare_corpus(comparison_case):
    """GIVEN changed findings WHEN compared THEN report each changed file."""
    harness, actual, expected, _path = comparison_case
    return harness.compare(actual, expected)


@then("the comparison report names that document")
def changed_path(comparison_case, comparison_report):
    """GIVEN a code change WHEN reported THEN name its source document."""
    expected = comparison_case[-1]
    assert expected in comparison_report


@given("the slop_away repository root", target_fixture="cli")
def repository_cli():
    """GIVEN the repository WHEN checked THEN use its project settings."""
    return CliHarness(REPO_ROOT)
