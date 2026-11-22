"""Check the STE writing rule subset."""

import re
from collections.abc import Iterator
from pathlib import Path

from slop_away.config import Config
from slop_away.findings import Finding, make_finding
from slop_away.markdown import Document
from slop_away.parsing import (
    PARSER,
    SUBJECT,
    ParsedToken,
    Sentence,
    is_imperative,
)
from slop_away.text import word_matches

CONTRACTION = re.compile(
    r"(?:\w+n['’]t|\w+['’](?:re|ve|ll|d|m|s))", re.IGNORECASE
)
FIXED_FORMS = {
    "it's",
    "that's",
    "there's",
    "here's",
    "what's",
    "who's",
    "where's",
    "when's",
    "how's",
    "he's",
    "she's",
    "let's",
}
PASSIVE = {"nsubjpass", "csubjpass", "auxpass", "nsubj:pass", "aux:pass"}
MESSAGES = {
    "STE003": ("Passive voice in the sentence.", "Use active voice."),
    "STE004": ("Contraction in prose.", "Write the words in full."),
    "STE005": (
        "Verb construction is not in a simple tense.",
        "Use the present, past, or future simple tense.",
    ),
    "STE006": (
        "Noun cluster has more than three nouns.",
        "Divide the noun cluster or add a preposition.",
    ),
}


def _contractions(sentence: Sentence) -> Iterator[int]:
    """Find contractions in a sentence.

    Args:
        sentence: The annotated sentence.

    Yields:
        Source offsets of contractions.
    """
    for word in word_matches(sentence.prose.text):
        value = word.group().casefold()
        if not CONTRACTION.fullmatch(value):
            continue
        start = sentence.prose.offsets[word.start()]
        end = sentence.prose.offsets[word.end() - 1] + 1
        parts = [
            token
            for token in sentence.tokens
            if start <= token.offset and token.end <= end
        ]
        if (
            not value.endswith("'s")
            or value in FIXED_FORMS
            or any(
                token.pos == "AUX" or token.dependency in SUBJECT
                for token in parts
            )
        ):
            yield start


def _clusters(tokens: tuple[ParsedToken, ...]) -> Iterator[int]:
    """Find long noun clusters.

    Args:
        tokens: Annotated words and punctuation.

    Yields:
        Source offsets of clusters with more than three nouns.
    """
    length = 0
    start = 0
    for token in tokens:
        if token.pos in {"NOUN", "PROPN"}:
            if length == 0:
                start = token.offset
            length += 1
            if length == 4:
                yield start
        else:
            length = 0


def _grammar(sentence: Sentence, config: Config) -> list[tuple[str, int]]:
    """Check sentence grammar.

    Args:
        sentence: The annotated sentence.
        config: The document settings.

    Returns:
        Rule codes and source offsets for grammar findings.
    """
    matches = []
    passive = {
        token.head for token in sentence.tokens if token.dependency in PASSIVE
    }
    if config.enabled("STE003"):
        for token in sentence.tokens:
            if token.index in passive:
                matches.append(("STE003", token.offset))
                break
    if config.enabled("STE004"):
        matches.extend(
            ("STE004", offset) for offset in _contractions(sentence)
        )
    if config.enabled("STE005"):
        by_index = {token.index: token for token in sentence.tokens}
        subjects = [
            by_index[token.head]
            for token in sentence.tokens
            if token.text == "'s"
            and token.dependency == "case"
            and token.head in by_index
            and by_index[token.head].dependency in SUBJECT
        ]
        for token in sentence.tokens:
            auxiliaries = [
                child
                for child in sentence.tokens
                if child.head == token.index
                and child.dependency in {"aux", "auxpass"}
            ]
            lemmas = {child.lemma for child in auxiliaries}
            contracted = [
                subject for subject in subjects if subject.head == token.index
            ]
            if contracted:
                lemmas.add(
                    "have"
                    if token.tag == "VBN" and token.index not in passive
                    else "be"
                )
            progressive = (
                token.tag == "VBG"
                and "be" in lemmas
                or any(
                    child.lemma == "be" and child.tag == "VBG"
                    for child in auxiliaries
                )
                and (
                    bool(contracted)
                    or any(
                        child.lemma == "be" and child.tag != "VBG"
                        for child in auxiliaries
                    )
                )
            )
            if "have" in lemmas or progressive:
                matches.append(("STE005", token.offset))
                break
    if config.enabled("STE006"):
        matches.extend(
            ("STE006", offset) for offset in _clusters(sentence.tokens)
        )
    return matches


def scan_ste(
    text: str, path: Path, config: Config, document: Document
) -> list[Finding]:
    """Check the STE rule subset.

    Args:
        text: The Markdown source.
        path: The source path.
        config: The document settings.
        document: The extracted Markdown text.

    Returns:
        STE findings with source locations and correction hints.
    """
    findings: list[Finding] = []
    if not any(config.enabled(f"STE{number:03}") for number in range(1, 8)):
        return findings
    terms = [
        (
            preferred,
            synonym,
            re.compile(
                r"(?<!\w)"
                + r"\s+".join(re.escape(part) for part in synonym.split())
                + r"(?!\w)",
                re.IGNORECASE,
            ),
        )
        for preferred, synonyms in config.glossary.items()
        for synonym in synonyms
    ]
    for block in document.blocks:
        sentences = PARSER.parse(block.prose)
        if (
            config.enabled("STE002")
            and block.kind != "heading"
            and len(sentences) > 6
        ):
            findings.append(
                make_finding(
                    "STE002",
                    sentences[0].prose.offsets[0],
                    text,
                    path,
                    " ".join(sentence.prose.text for sentence in sentences),
                    f"Paragraph has {len(sentences)} sentences; "
                    "the limit is 6.",
                    "Divide the paragraph into shorter paragraphs.",
                )
            )
        for sentence in sentences:
            words = len(word_matches(sentence.prose.text))
            limit = 20 if block.procedure or is_imperative(sentence) else 25
            if config.enabled("STE001") and words > limit:
                findings.append(
                    make_finding(
                        "STE001",
                        sentence.prose.offsets[0],
                        text,
                        path,
                        sentence.prose.text,
                        f"Sentence has {words} words; the limit is {limit}.",
                        "Divide the sentence into shorter sentences.",
                    )
                )
            for code, offset in _grammar(sentence, config):
                findings.append(
                    make_finding(
                        code,
                        offset,
                        text,
                        path,
                        sentence.prose.text,
                        *MESSAGES[code],
                    )
                )
            if config.enabled("STE007"):
                for preferred, synonym, pattern in terms:
                    for match in pattern.finditer(sentence.prose.text):
                        findings.append(
                            make_finding(
                                "STE007",
                                sentence.prose.offsets[match.start()],
                                text,
                                path,
                                sentence.prose.text,
                                f"Term {synonym!r} is not the preferred term.",
                                f"Use {preferred!r} instead of {synonym!r}.",
                            )
                        )
    return findings
