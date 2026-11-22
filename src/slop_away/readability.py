"""Check section readability."""

from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

from syllapy import count  # type: ignore[import-untyped]

from slop_away.config import Config
from slop_away.findings import Finding, make_finding
from slop_away.markdown import Block, Document
from slop_away.text import split_sentences, word_matches


def _sections(document: Document) -> Iterator[tuple[Block, list[Block]]]:
    """Get paragraph prose in each h2 section.

    Args:
        document: The extracted Markdown text.

    Yields:
        Each h2 heading with its paragraphs.
    """
    heading = None
    paragraphs: list[Block] = []
    for block in document.blocks:
        if block.kind == "heading" and block.level <= 2:
            if heading is not None:
                yield heading, paragraphs
            heading = block if block.level == 2 else None
            paragraphs = []
        elif heading is not None and block.kind == "paragraph":
            paragraphs.append(block)
    if heading is not None:
        yield heading, paragraphs


def scan_readability(
    text: str, path: Path, config: Config, document: Document
) -> list[Finding]:
    """Check the readability of h2 sections.

    Args:
        text: The Markdown source.
        path: The source path.
        config: The document settings.
        document: The extracted Markdown text.

    Returns:
        Findings for sections above the grade limit.
    """
    findings: list[Finding] = []
    if not config.enabled("RDB001"):
        return findings
    for heading, paragraphs in _sections(document):
        sentences = [
            sentence
            for block in paragraphs
            for sentence in split_sentences(block.prose)
            if any(char.isalpha() for char in sentence.text)
        ]
        syllables = [
            count(match.group().casefold())
            for sentence in sentences
            for match in word_matches(sentence.text)
            if any(char.isalpha() for char in match.group())
        ]
        if not syllables:
            continue
        grade = (
            Decimal("0.39") * len(syllables) / len(sentences)
            + Decimal("11.8") * sum(syllables) / len(syllables)
            - Decimal("15.59")
        )
        if grade > Decimal(str(config.max_grade)):
            context = "\n".join(
                block.prose.text for block in (heading, *paragraphs)
            )
            findings.append(
                make_finding(
                    "RDB001",
                    heading.offset,
                    text,
                    path,
                    context,
                    f"Section grade {grade:.2f} is above the limit "
                    f"{config.max_grade}.",
                    "Use shorter sentences and simpler words.",
                )
            )
    return findings
