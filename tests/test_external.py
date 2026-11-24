"""Check the pinned external corpus."""

import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from tests.generation.draw import ROOT, english, measure

SOURCES = json.loads((ROOT / "sources.json").read_text())


@pytest.fixture(params=SOURCES["documents"], ids=lambda item: item["file"])
def external_case(request):
    """GIVEN a pinned document WHEN checked THEN use its recorded source."""
    record = request.param
    source = (ROOT / record["file"]).read_bytes()
    return record, source


def test_external_english(external_case):
    """GIVEN a corpus document WHEN detected THEN its prose is English."""
    _record, source = external_case
    expected = True
    actual = english(source.decode("utf-8"))
    assert actual is expected


def test_external_measurements(external_case):
    """GIVEN a corpus document WHEN measured THEN match its source record."""
    record, source = external_case
    expected = record["words"], record["excluded_lines"], record["lines"]
    actual = measure(source.decode("utf-8"))
    assert actual == expected


def test_external_hash(external_case):
    """GIVEN pinned source bytes WHEN hashed THEN match their record."""
    record, source = external_case
    actual = hashlib.sha256(source).hexdigest()
    assert actual == record["sha256"]


@pytest.fixture
def quota_case():
    """GIVEN corpus groups WHEN counted THEN meet all required quotas."""
    expected = Counter(
        {
            (kind, era): count
            for kind, old, new in (
                ("readme", 3, 3),
                ("contributor", 2, 2),
                ("changelog", 2, 2),
                ("roadmap", 2, 2),
                ("design", 2, 2),
                ("agent", 0, 4),
                ("tutorial", 2, 2),
            )
            for era, count in (("old", old), ("new", new))
            if count
        }
    )
    return SOURCES["documents"], expected


def test_external_quotas(quota_case):
    """GIVEN the corpus WHEN counted THEN meet each type and era quota."""
    documents, expected = quota_case
    actual = Counter((item["type"], item["era"]) for item in documents)
    assert actual == expected


@pytest.fixture(params=SOURCES["documents"], ids=lambda item: item["file"])
def eligible_case(request):
    """GIVEN a source record WHEN checked THEN meet every draw limit."""
    item = request.param
    directory = ROOT / "licenses" / Path(item["file"]).stem
    return item, directory, True


def test_external_eligibility(eligible_case):
    """GIVEN a selected record WHEN inspected THEN meet the fixed limits."""
    item, directory, expected = eligible_case
    actual = (
        item["words"] >= 150
        and item["excluded_lines"] * 2 <= item["lines"]
        and item["stars"] >= 20
        and any(directory.iterdir())
        and (item["date"] < "2022" if item["era"] == "old" else item["date"] >= "2023")
    )
    assert actual is expected


@pytest.fixture
def replay_case():
    """GIVEN recorded draws WHEN replayed THEN retain the same source choices."""
    from tests.generation.draw import draw

    selected = {
        (item["repo"], item["commit"], item["path"]): item
        for item in SOURCES["documents"]
    }
    attempts = {
        (item["repo"], item["commit"], item["path"]): item
        for item in SOURCES["attempts"]
    }

    def read(item):
        """GIVEN a draw WHEN replayed THEN use its recorded eligibility class."""
        key = item["repo"], item["commit"], item["path"]
        reason = attempts[key]["rejection"]
        if reason is None:
            return (ROOT / selected[key]["file"]).read_bytes()
        if reason == "fewer than 150 prose words":
            return b"The file is short."
        if reason == "non-English prose":
            return (
                "Les utilisateurs lisent les fichiers dans le dossier. " * 30
            ).encode()
        if reason == "excluded lines exceed half":
            return (
                "The tool reads each file. " * 40 + "\n```\n" + "x\n" * 10 + "```\n"
            ).encode()
        raise ValueError(f"Unexpected read for rejected source: {reason}.")

    return draw, read, SOURCES["seed"], SOURCES["attempts"]


def test_seeded_replay(replay_case):
    """GIVEN the seed and rejection classes WHEN drawn THEN repeat the choices."""
    draw, reader, seed, expected = replay_case
    _selected, actual = draw(seed, reader)
    assert actual == expected
