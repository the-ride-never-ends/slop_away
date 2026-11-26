"""Describe rule findings."""

import hashlib
import re
from bisect import bisect_left
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    """Hold one rule finding and its source location."""

    code: str
    path: Path
    line: int
    column: int
    message: str
    hint: str
    fingerprint: str


@lru_cache(maxsize=1)
def _line_breaks(text: str) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Get line boundaries in source text.

    Args:
        text: The source text.

    Returns:
        The start and end of each line break.
    """
    boundaries = tuple(re.finditer(r"\r\n|\r|\n", text))
    return (
        tuple(match.start() for match in boundaries),
        tuple(match.end() for match in boundaries),
    )


def make_finding(
    *,
    code: str,
    offset: int,
    text: str,
    path: Path,
    context: str,
    message: str,
    hint: str,
) -> Finding:
    """Describe a rule finding.

    Args:
        code: The rule code.
        offset: The source offset.
        text: The source text.
        path: The source path.
        context: The sentence or section text.
        message: The finding message.
        hint: The correction hint.

    Returns:
        The finding with its source location and fingerprint.
    """
    normalized = " ".join(context.casefold().split())
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    fingerprint = f"{code}:{path.as_posix()}:{digest}"
    starts, ends = _line_breaks(text)
    count = bisect_left(starts, offset)
    line = count + 1
    column = offset - (min(ends[count - 1], offset) if count else 0) + 1
    return Finding(
        code=code,
        path=path,
        line=line,
        column=column,
        message=message,
        hint=hint,
        fingerprint=fingerprint,
    )
