"""Supply the slop_away command."""

import logging
import sys
from argparse import ArgumentParser
from collections.abc import Sequence
from importlib.metadata import version
from pathlib import Path

from slop_away.checks import check_files, fix_files
from slop_away.config import ConfigError, find_root, load_config
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
        "--output-format", choices=("text", "agent"), default="text"
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
        paths = [str(Path.cwd() / path) for path in args.paths]
        findings = (
            fix_files(paths, config, args.unsafe_fixes)
            if args.fix or args.unsafe_fixes
            else check_files(paths, config)
        )
        for finding in findings:
            location = (
                f"{finding.path.as_posix()}:{finding.line}:{finding.column}"
            )
            if args.output_format == "agent":
                print(
                    f"{finding.code} {location} {finding.message} "
                    f"Fix: {finding.hint}"
                )
            else:
                print(f"{location}: {finding.code} {finding.message}")
        return int(bool(findings))
    except (ConfigError, OSError, UnicodeError, ValueError) as error:
        print(f"slop_away: {error}", file=sys.stderr)
        return 2
    except Exception:
        LOGGER.exception("slop_away internal error.")
        return 2
