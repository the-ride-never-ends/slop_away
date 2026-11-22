"""Supply the slop_away command."""

import logging
import sys
from argparse import ArgumentParser
from collections.abc import Sequence
from importlib.metadata import version
from pathlib import Path

from slop_away.baseline import Baseline, load_baseline, write_baseline
from slop_away.checks import check_files, fix_files
from slop_away.config import ConfigError, find_root, load_config
from slop_away.output import render_findings
from slop_away.packages import sync_packages

LOGGER = logging.getLogger(__name__)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command.

    Args:
        argv: Command arguments. Use process arguments if None.

    Returns:
        The exit code.
    """
    parser = ArgumentParser(
        prog="slop_away",
        description="Check documentation and commit messages.",
    )
    parser.add_argument(
        "--version", action="version", version=version("slop_away")
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("sync", help="Download configured rule packages.")
    check = commands.add_parser("check", help="Check Markdown files.")
    check.add_argument("paths", nargs="*", default=["."])
    check.add_argument("--fix", action="store_true", help="Apply safe fixes.")
    check.add_argument(
        "--unsafe-fixes",
        action="store_true",
        help="Also apply fixes that can change meaning.",
    )
    check.add_argument(
        "--write-baseline",
        action="store_true",
        help="Record current findings as the baseline.",
    )
    check.add_argument(
        "--output-format",
        choices=("text", "agent", "json", "github"),
        default="text",
    )
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        config = load_config(find_root(Path.cwd()))
        if args.command == "sync":
            sync_packages(config)
            return 0
        baseline = (
            Baseline() if args.write_baseline else load_baseline(config.root)
        )
        paths = [str(Path.cwd() / path) for path in args.paths]
        findings = (
            fix_files(paths, config, args.unsafe_fixes)
            if args.fix or args.unsafe_fixes
            else check_files(paths, config)
        )
        if args.write_baseline:
            baseline = write_baseline(config.root, findings)
        findings = [
            finding for finding in findings if not baseline.matches(finding)
        ]
        print(render_findings(findings, args.output_format), end="")
        return int(bool(findings))
    except (ConfigError, OSError, UnicodeError, ValueError) as error:
        print(f"slop_away: {error}", file=sys.stderr)
        return 2
    except Exception:
        LOGGER.exception("slop_away internal error.")
        return 2
