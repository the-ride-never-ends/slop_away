"""Describe rule findings."""

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
