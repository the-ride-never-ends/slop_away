"""Check section readability."""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from functools import cache
from pathlib import Path

import cmudict
import pyphen  # type: ignore[import-untyped]

from slop_away.config import Config
from slop_away.utils.findings import Finding, make_finding
from slop_away.utils.markdown import Block, Document, parse_document


def _sections(doc: Document) -> Iterator[tuple[Block, list[Block]]]:
    """Get paragraph prose in each h2 section.

    Args:
        doc: The extracted Markdown text.

    Yields:
        Each h2 heading with its paragraphs.
    """
    heading = None
    paragraphs: list[Block] = []
    for block in doc.blocks:
        if block.kind == "heading" and block.level <= 2:
            if heading is not None:
                yield heading, paragraphs
            heading = block if block.level == 2 else None
            paragraphs = []
        elif heading is not None and block.kind == "paragraph":
            paragraphs.append(block)
    if heading is not None:
        yield heading, paragraphs


@dataclass(frozen=True)
class SectionGrade:
    """Hold a section heading, prose, and Flesch-Kincaid grade."""

    heading: str
    prose: str
    line: int
    grade: Decimal


def _words(text: str) -> list[str]:
    """Get alphabetic scoring words.

    Args:
        text: The visible section prose.

    Returns:
        Words without punctuation or numeric-only tokens.
    """
    text = re.sub(r"(?<!\w)'|'(?!\w)", "", text)
    text = re.sub(r"[^\w\s']", "", text)
    return [word for word in text.split() if any(char.isalpha() for char in word)]


@cache
def _dictionary() -> dict[str, list[list[str]]]:
    """Get the installed English pronunciation dictionary.

    Returns:
        Words and their phoneme sequences.
    """
    return cmudict.dict()


@cache
def _hyphenator() -> pyphen.Pyphen:
    """Get the English pattern data for unknown words.

    Returns:
        The English hyphenation patterns.
    """
    return pyphen.Pyphen(lang="en_US")


@cache
def _syllables(word: str) -> int:
    """Count pronunciation syllables or unknown-word segments.

    Args:
        word: The scoring word in lowercase.

    Returns:
        The syllable count.
    """
    pronunciations = _dictionary().get(word)
    if pronunciations:
        return sum(phoneme[-1].isdigit() for phoneme in pronunciations[0])
    return len(_hyphenator().positions(word)) + 1


def _graded(
    doc: Document,
) -> Iterator[tuple[Block, list[Block], str, Decimal]]:
    """Score eligible section prose.

    Args:
        doc: The parsed document.

    Yields:
        The heading, paragraphs, prose, and grade.
    """
    for heading, paragraphs in _sections(doc):
        prose = "\n\n".join(block.prose.text.strip() for block in paragraphs)
        prose = re.sub(r"(?<!\w)\d+(?:[.,]\d+)*(?!\w)", "", prose).replace("’", "'")
        words = _words(prose)
        if not words:
            continue
        regions = re.findall(r"\b[^.!?]+[.!?]*", prose)
        sentences = max(1, sum(len(_words(region)) > 2 for region in regions))
        syllables = sum(_syllables(word.casefold()) for word in words)
        grade = (
            Decimal("0.39") * len(words) / sentences
            + Decimal("11.8") * syllables / len(words)
            - Decimal("15.59")
        )
        yield heading, paragraphs, prose, grade


def grade_sections(text: str) -> list[SectionGrade]:
    """Get readability grades for eligible h2 sections.

    Args:
        text: The Markdown source.

    Returns:
        Section grades in source order, without a grade limit.
    """
    return [
        SectionGrade(
            heading=heading.prose.text.strip(),
            prose=prose,
            line=len(re.findall(r"\r\n|\r|\n", text[: heading.offset])) + 1,
            grade=grade,
        )
        for heading, _, prose, grade in _graded(parse_document(text))
    ]


def scan_readability(
    text: str, path: Path, config: Config, doc: Document
) -> list[Finding]:
    """Check the readability of h2 sections.

    Args:
        text: The Markdown source.
        path: The source path.
        config: The document settings.
        doc: The extracted Markdown text.

    Returns:
        Findings for sections above the grade limit.
    """
    findings: list[Finding] = []
    if not config.enabled("RDB001"):
        return findings
    for heading, paragraphs, _, grade in _graded(doc):
        if grade > Decimal(str(config.max_grade)):
            context = "\n".join(block.prose.text for block in (heading, *paragraphs))
            findings.append(
                make_finding(
                    code="RDB001",
                    offset=heading.offset,
                    text=text,
                    path=path,
                    context=context,
                    message=f"Section grade {grade:.2f} is above the limit "
                    f"{config.max_grade}.",
                    hint="Use shorter sentences and simpler words.",
                )
            )
    return findings
