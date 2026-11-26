"""Count prose words and identify sentences."""

import re

from slop_away.utils.markdown import Projection

WORD = re.compile(r"\d+(?:[.,]\d+)*|[^\W_]+(?:['’\-][^\W_]+)*")
ENDING = re.compile(r"[.!?]+[\"'’”)*_~\]]*(?=\s|$)")
ABBREVIATIONS = {
    "e.g.",
    "i.e.",
    "mr.",
    "mrs.",
    "ms.",
    "dr.",
    "prof.",
    "vs.",
    "etc.",
}


def word_matches(text: str) -> list[re.Match[str]]:
    """Find words in prose.

    Args:
        text: The prose text.

    Returns:
        Word matches in text order.
    """
    return list(WORD.finditer(text))


def split_sentences(projection: Projection) -> list[Projection]:
    """Divide a prose block into sentences.

    Args:
        projection: The prose block with source offsets.

    Returns:
        Sentences with their source offsets.
    """
    source = projection.text
    boundaries = []
    for match in ENDING.finditer(source):
        prefix = source[: match.end()].split()
        last = prefix[-1].casefold() if prefix else ""
        if last not in ABBREVIATIONS and not re.fullmatch(r"(?:[a-z]\.){2,}", last):
            boundaries.append(match.end())
    boundaries.append(len(source))
    sentences = []
    start = 0
    for end in boundaries:
        content = source[start:end]
        left = start + len(content) - len(content.lstrip())
        right = end - len(content) + len(content.rstrip())
        if word_matches(source[left:right]):
            sentences.append(
                Projection(source[left:right], projection.offsets[left:right])
            )
        start = end
    return sentences
