"""Check text for injection patterns."""

import re
import unicodedata
from collections.abc import Iterator
from datetime import date
from pathlib import Path

from slop_away.config import Config
from slop_away.findings import Finding, make_finding
from slop_away.markdown import Document, Projection

GAP = r"[*_~]*\s+[*_~]*"
DIRECTIVE = re.compile(
    rf"\byou{GAP}(?:must|should|shall|need{GAP}to|have{GAP}to)\b"
    rf"|\b(?:always|never){GAP}\w+"
    rf"|\bdo{GAP}not{GAP}\w+|\bimportant[*_~]*\s*:[*_~]*\s*\w+",
    re.IGNORECASE,
)
ROLE = re.compile(
    r"\b(?:system|assistant|user|developer)[*_~]*\s*:", re.IGNORECASE
)
ACTION = re.compile(
    r"^[ \t]*(?:[-*+]\s+\[[ xX]\]|TODO\b|Next\s+step\b)[^\n]*",
    re.IGNORECASE | re.MULTILINE,
)
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
STATUS = re.compile(
    r"\[[xX]\]|\((?:doing|blocked|done|pending|open|closed|complete)"
    r"\b[^)\n]*\)|\bstatus\s*:\s*"
    r"(?:doing|blocked|done|pending|open|closed|complete)\b",
    re.IGNORECASE,
)
MESSAGES = {
    "INJ001": (
        "Directive addressed to the reader.",
        "Remove the directive or move it to an instruction file.",
    ),
    "INJ002": (
        "Role marker in document text.",
        "Remove the role marker or put the example in a code block.",
    ),
    "INJ003": (
        "Action item has no status or date.",
        "Add a status or a date to the action item.",
    ),
    "INJ004": (
        "Hidden text in the document.",
        "Remove the invisible character or correct the HTML comment.",
    ),
}


def _dated(text: str) -> bool:
    """Check for a valid action date.

    Args:
        text: The action text.

    Returns:
        True if the action has a valid date.
    """
    for match in DATE.finditer(text):
        try:
            date.fromisoformat(match.group())
        except ValueError:
            continue
        return True
    return False


def _directives(text: str) -> Iterator[re.Match[str]]:
    """Find directives addressed to the reader.

    Args:
        text: The text to check.

    Yields:
        Directive matches.
    """
    for match in DIRECTIVE.finditer(text):
        if re.match(r"you\b|important\b", match.group(), re.IGNORECASE):
            yield match
        else:
            prefix = re.split(r"[.!?\n]", text[: match.start()])[-1]
            if not re.search(r"\w", prefix):
                yield match


def _context(projection: Projection, start: int) -> str:
    """Get the text for a finding.

    Args:
        projection: The text being checked.
        start: The match offset.

    Returns:
        The sentence or action text.
    """
    source = projection.text
    left = max(source.rfind(char, 0, start) for char in ".!?\n") + 1
    boundary = re.search(r"[.!?\n]", source[start:])
    right = start + boundary.end() if boundary else len(source)
    return source[left:right]


def scan_injection(
    text: str, path: Path, config: Config, document: Document
) -> list[Finding]:
    """Check the injection rules.

    Args:
        text: The Markdown source.
        path: The source path.
        config: The project settings.
        document: The extracted Markdown text.

    Returns:
        Findings in source order.
    """
    findings: list[Finding] = []
    instruction = path.name in config.instruction_files
    for projection in (document.prose, *document.comments):
        comment = projection is not document.prose
        matches: list[tuple[str, int]] = []
        if comment or not instruction:
            code = "INJ004" if comment else "INJ001"
            matches.extend(
                (code, match.start()) for match in _directives(projection.text)
            )
        matches.extend(
            ("INJ002", match.start())
            for match in ROLE.finditer(projection.text)
        )
        for match in ACTION.finditer(projection.text):
            if not _dated(match.group()) and not STATUS.search(match.group()):
                matches.append(("INJ003", match.start()))
        matches.extend(
            ("INJ004", index)
            for index, char in enumerate(projection.text)
            if unicodedata.category(char) == "Cf"
        )
        for code, index in matches:
            if config.enabled(code):
                findings.append(
                    make_finding(
                        code,
                        projection.offsets[index],
                        text,
                        path,
                        _context(projection, index),
                        *MESSAGES[code],
                    )
                )
    return sorted(
        findings, key=lambda item: (item.line, item.column, item.code)
    )
