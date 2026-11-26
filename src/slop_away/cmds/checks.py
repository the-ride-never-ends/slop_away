"""Check project Markdown files."""

from collections.abc import Sequence
from pathlib import Path

from slop_away.cmds.helpers.external import scan_external
from slop_away.cmds.helpers.fixes import fix_text
from slop_away.cmds.helpers.packages import load_rules
from slop_away.cmds.helpers.rules.injection import scan_injection
from slop_away.cmds.helpers.rules.readability import scan_readability
from slop_away.cmds.helpers.rules.schema import Rule
from slop_away.cmds.helpers.rules.ste import scan_ste
from slop_away.cmds.helpers.rules.verbosity import scan_verbosity
from slop_away.config import Config
from slop_away.utils.findings import Finding
from slop_away.utils.markdown import parse_document
from slop_away.utils.selection import select_files
from slop_away.utils.write import write_text


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

    kwargs = {
        "path": path,
        "text": text,
        "config": settings,
        "doc": parse_document(text),
    }

    findings = scan_injection(**kwargs)
    if path.name not in settings.instruction_files:
        findings.extend(scan_verbosity(**kwargs, seen=seen))
        findings.extend(scan_readability(**kwargs))
        findings.extend(scan_ste(**kwargs))
        findings.extend(scan_external(**kwargs, rules=rules))
    return sorted(findings, key=lambda item: (item.line, item.column, item.code))


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


def check_files(
    *, paths: Sequence[str | Path], config: Config, force_exclude: bool = False
) -> list[Finding]:
    """Check selected Markdown files.

    Args:
        paths: Project paths or glob patterns.
        config: The project settings.
        force_exclude: Apply excludes to files named directly.

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
    for path in select_files(paths=paths, config=config, force_exclude=force_exclude):
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
    *,
    paths: Sequence[str | Path],
    config: Config,
    unsafe: bool = False,
    force_exclude: bool = False,
) -> list[Finding]:
    """Fix selected files and report the remaining findings.

    Args:
        paths: Project paths or glob patterns.
        config: The project settings.
        unsafe: Permit changes that can change meaning.
        force_exclude: Apply excludes to files named directly.

    Returns:
        Findings in the changed files, in path and source order.

    Raises:
        OSError: A file cannot be read or replaced.
        UnicodeError: An input is not UTF-8 text.
        ValueError: An input, package cache, or fix plan is invalid.
        TypeError: The unsafe option is not a boolean.
    """
    rules = load_rules(config)
    pending = []
    findings = []
    seen: dict[str, Path] = {}
    for path in select_files(paths=paths, config=config, force_exclude=force_exclude):
        with path.open(encoding="utf-8", newline="") as f:
            source = f.read()
        relative = path.relative_to(config.root)
        changed = fix_text(
            text=source,
            path=relative,
            config=config,
            unsafe=unsafe,
            rules=rules,
        )
        findings.extend(_check(changed, relative, config, seen, rules))
        if changed != source:
            pending.append((path, changed))
    for path, changed in pending:
        write_text(path=path, text=changed)
    return findings
