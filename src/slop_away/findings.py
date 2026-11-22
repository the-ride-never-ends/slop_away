"""Describe rule findings."""

import hashlib
import re
from dataclasses import dataclass
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


def make_finding(
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
    breaks = list(re.finditer(r"\r\n|\r|\n", text[:offset]))
    line = len(breaks) + 1
    column = offset - (breaks[-1].end() if breaks else 0) + 1
    return Finding(code, path, line, column, message, hint, fingerprint)
