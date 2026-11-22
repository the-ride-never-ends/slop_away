"""Check project Markdown files."""

from collections.abc import Sequence
from pathlib import Path

from slop_away.config import Config
from slop_away.external import scan_external
from slop_away.findings import Finding
from slop_away.fixes import fix_text
from slop_away.injection import scan_injection
from slop_away.markdown import parse_document
from slop_away.packages import load_rules
from slop_away.readability import scan_readability
from slop_away.rule_schema import Rule
from slop_away.selection import select_files
from slop_away.ste import scan_ste
from slop_away.storage import write_text
from slop_away.verbosity import scan_verbosity


def _check(
    text: str,
    path: Path,
    config: Config,
    seen: dict[str, Path],
    rules: tuple[Rule, ...],
) -> list[Finding]:
    """Check a document with settings for its path.

    Args:
        text: The Markdown source.
        path: The source path.
        config: The project settings.
        seen: Sentences from files checked in this run.
        rules: The configured package rules.

    Returns:
        Findings in source order.
    """
    if path.is_absolute():
        path = path.relative_to(config.root)
    settings = config.for_path(path)
    document = parse_document(text)
    findings = scan_injection(text, path, settings, document)
    if path.name not in settings.instruction_files:
        findings.extend(scan_verbosity(text, path, settings, document, seen))
        findings.extend(scan_readability(text, path, settings, document))
        findings.extend(scan_ste(text, path, settings, document))
        findings.extend(scan_external(text, path, settings, document, rules))
    return sorted(
        findings, key=lambda item: (item.line, item.column, item.code)
    )


def check_text(text: str, path: str | Path, config: Config) -> list[Finding]:
    """Check Markdown text.

    Args:
        text: The Markdown source.
        path: The source path.
        config: The project settings.

    Returns:
        Findings in source order.

    Raises:
        ValueError: A configured package cache or selector is invalid.
    """
    return _check(text, Path(path), config, {}, load_rules(config))


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
    rules = load_rules(config)
    findings = []
    seen: dict[str, Path] = {}
    for path in select_files(paths, config):
        findings.extend(
            _check(
                path.read_text(encoding="utf-8"),
                path.relative_to(config.root),
                config,
                seen,
                rules,
            )
        )
    return findings


def fix_files(
    paths: Sequence[str | Path], config: Config, unsafe: bool = False
) -> list[Finding]:
    """Fix selected files and report the remaining findings.

    Args:
        paths: Project paths or glob patterns.
        config: The project settings.
        unsafe: Permit changes that can change meaning.

    Returns:
        Findings in the changed files, in path and source order.

    Raises:
        OSError: A file cannot be read or replaced.
        UnicodeError: An input is not UTF-8 text.
        ValueError: An input, package cache, or fix plan is invalid.
        TypeError: The unsafe option is not a boolean.
    """
    if not isinstance(unsafe, bool):
        raise TypeError("Expected a boolean unsafe option.")
    rules = load_rules(config)
    pending = []
    findings = []
    seen: dict[str, Path] = {}
    for path in select_files(paths, config):
        with path.open(encoding="utf-8", newline="") as stream:
            source = stream.read()
        relative = path.relative_to(config.root)
        changed = fix_text(source, relative, config, unsafe, rules)
        findings.extend(_check(changed, relative, config, seen, rules))
        if changed != source:
            pending.append((path, changed))
    for path, changed in pending:
        write_text(path, changed)
    return findings
