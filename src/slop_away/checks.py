"""Check project Markdown files."""

from collections.abc import Sequence
from pathlib import Path

from slop_away.config import Config
from slop_away.findings import Finding
from slop_away.injection import scan_injection
from slop_away.selection import select_files


def check_text(text: str, path: str | Path, config: Config) -> list[Finding]:
    """Check Markdown text.

    Args:
        text: The Markdown source.
        path: The source path.
        config: The project settings.

    Returns:
        Findings in source order.
    """
    return scan_injection(text, Path(path), config)


def check_files(paths: Sequence[str | Path], config: Config) -> list[Finding]:
    """Check selected Markdown files.

    Args:
        paths: Project paths or glob patterns.
        config: The project settings.

    Returns:
        Findings in path and source order.

    Raises:
        OSError: An input cannot be read.
        UnicodeError: An input is not UTF-8 text.
        ValueError: An input is outside the project.
    """
    findings = []
    for path in select_files(paths, config):
        findings.extend(
            check_text(
                path.read_text(encoding="utf-8"),
                path.relative_to(config.root),
                config,
            )
        )
    return findings
