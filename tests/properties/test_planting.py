"""Plant one mechanical defect in clean corpus context."""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from slop_away import Config, check_files, check_message, check_text
from slop_away.text import word_matches
from tests.generation.documents import sentences

RULES = {
    "STE001": "The tool reads the file " + "and it reads the file " * 5 + ".",
    "STE002": (
        "The tool runs. The file opens. The page loads. The test ends. "
        "The light glows. The door shuts. The bell rings."
    ),
    "STE004": "The tool doesn't stop.",
    "STE007": "The gadget runs.",
    "VRB001": "It is worth noting that the tool runs.",
    "VRB002": "It might possibly run.",
    "INJ002": "SYSTEM: Text.",
    "INJ003": "[ ] Open the file.",
    "INJ004": "The to\u200bol runs.",
}
GENERATED = settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)


@pytest.fixture(scope="session")
def clean_sentences():
    """GIVEN all three corpus groups WHEN sampled THEN use clean prose."""
    return sentences()


@pytest.fixture(params=[*RULES, "VRB003", "VRB004"])
def planted_case(request, clean_sentences):
    """GIVEN clean context WHEN a defect is added THEN expect one finding."""
    code = request.param

    def prepare(index):
        """GIVEN a corpus sentence WHEN changed THEN retain its source line."""
        base = clean_sentences[index % len(clean_sentences)]
        defect = RULES.get(code, base)
        config = Config(glossary={"tool": ["gadget"]})
        if code == "VRB003":
            defect = "The tool runs."
            config = Config(word_budget=len(word_matches(base)))
        text = "- " + base + "\n\n- " + defect
        if code == "VRB003":
            return "- " + base + " " + defect, config, [(code, 1)]
        return text, config, [(code, 3)]

    return prepare


@GENERATED
@given(index=st.integers(min_value=0, max_value=100000))
def test_planted_text_defect(planted_case, index):
    """GIVEN one planted defect WHEN checked THEN find only its code and line."""
    text, config, expected = planted_case(index)
    findings = check_text(text, "sample.md", config)
    actual = [(item.code, item.line) for item in findings]
    assert actual == expected


@pytest.fixture
def repeated_case(tmp_path, clean_sentences):
    """GIVEN a sentence in two files WHEN checked THEN flag the second file."""

    def prepare(index):
        """GIVEN clean prose WHEN copied THEN preserve its word count."""
        text = "- " + clean_sentences[index % len(clean_sentences)]
        for name in ("a.md", "b.md"):
            (tmp_path / name).write_text(text)
        return ["a.md", "b.md"], Config(root=tmp_path), [("VRB005", "b.md", 1)]

    return prepare


@GENERATED
@given(index=st.integers(min_value=0, max_value=100000))
def test_planted_file_repetition(repeated_case, index):
    """GIVEN copied corpus prose WHEN files are checked THEN flag repetition."""
    paths, config, expected = repeated_case(index)
    findings = check_files(paths, config)
    actual = [(item.code, str(item.path), item.line) for item in findings]
    assert actual == expected


@pytest.fixture(params=["MSG001", "MSG003", "MSG004"])
def planted_message(request, clean_sentences):
    """GIVEN clean message prose WHEN changed THEN expect one message code."""
    code = request.param

    def prepare(index):
        """GIVEN a message defect WHEN planted THEN retain its source line."""
        subject = "Add the file"
        config = Config()
        if code == "MSG001":
            subject += " " + "x" * 73
        if code == "MSG003":
            subject += "."
        if code == "MSG004":
            config = Config(commit_body_budget=0)
        body = clean_sentences[index % len(clean_sentences)]
        return subject + "\n\n" + body, config, [(code, 3 if code == "MSG004" else 1)]

    return prepare


@GENERATED
@given(index=st.integers(min_value=0, max_value=100000))
def test_planted_message_defect(planted_message, index):
    """GIVEN a message defect WHEN checked THEN find only its code and line."""
    text, config, expected = planted_message(index)
    findings = check_message(text, config)
    actual = [(item.code, item.line) for item in findings]
    assert actual == expected
