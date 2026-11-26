"""Supply the slop_away command."""

import logging
import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from collections.abc import Sequence
from importlib.metadata import version
from pathlib import Path

from slop_away.cmds import (
    Baseline,
    check_files,
    check_message,
    fix_files,
    guard_command,
    init_project,
    load_baseline,
    render_findings,
    sync_packages,
    write_baseline,
)
from slop_away.config import ConfigError, find_root, load_config
from slop_away.utils.selection import select_files

logger = logging.getLogger(__name__)

MAIN_EXAMPLES = """\
examples:
  slop_away init                  set up config, pre-commit, CI, and hooks
  slop_away check                 check every Markdown file in the project
  slop_away check README.md docs  check some files and folders
  slop_away check --fix           apply safe fixes, then report the rest
  slop_away check --commit-msg .git/COMMIT_EDITMSG

exit codes:
  0  no findings
  1  findings
  2  error

Run "slop_away COMMAND --help" for the options of one command.
"""

INIT_EXAMPLES = """\
examples:
  slop_away init                  add everything
  slop_away init --skip-ci        add everything except the CI workflow
  slop_away init --skip-hooks --skip-pre-commit
                                  add only the config and the CI workflow
"""

SYNC_EXAMPLES = """\
examples:
  slop_away sync                  download the packages in slop_away.toml
"""

GUARD_EXAMPLES = """\
examples:
  slop_away guard "git commit -m 'Fix typo'"
                                  exits 0: the hooks run
  slop_away guard "git commit --no-verify -m 'Fix typo'"
                                  exits 2: the command skips the hooks
"""

CHECK_EXAMPLES = """\
examples:
  slop_away check                 check the whole project
  slop_away check docs/ AGENTS.md check some files and folders
  slop_away check --fix README.md apply safe fixes to one file
  slop_away check --unsafe-fixes  also apply fixes that can change meaning
  slop_away check --commit-msg .git/COMMIT_EDITMSG
                                  check a commit message
  slop_away check --write-baseline
                                  accept the current findings
  slop_away check --output-format github
                                  report findings as GitHub annotations
  slop_away check --force-exclude tests/corpus/bad/AGENTS.md
                                  skip a named file that an exclude matches

A file named directly is checked even when an exclude or .gitignore
matches it. Use --force-exclude in hooks that pass file names.
"""


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(
        prog="slop_away",
        description="Check documentation and commit messages.",
        epilog=MAIN_EXAMPLES,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=version("slop_away"))
    commands = parser.add_subparsers(dest="command")
    commands.add_parser(
        "sync",
        help="Download configured rule packages.",
        epilog=SYNC_EXAMPLES,
        formatter_class=RawDescriptionHelpFormatter,
    )
    setup = commands.add_parser(
        "init",
        help="Prepare project checks and hooks.",
        epilog=INIT_EXAMPLES,
        formatter_class=RawDescriptionHelpFormatter,
    )
    for part in ("config", "pre-commit", "ci", "hooks"):
        setup.add_argument(f"--skip-{part}", action="store_true")
    guard = commands.add_parser(
        "guard",
        help="Check a shell command for skipped commit hooks.",
        epilog=GUARD_EXAMPLES,
        formatter_class=RawDescriptionHelpFormatter,
    )
    guard.add_argument("shell_command")
    check = commands.add_parser(
        "check",
        help="Check Markdown files.",
        epilog=CHECK_EXAMPLES,
        formatter_class=RawDescriptionHelpFormatter,
    )
    check.add_argument("paths", nargs="*")
    check.add_argument(
        "--commit-msg", metavar="PATH", help="Check a commit-message file."
    )
    check.add_argument("--fix", action="store_true", help="Apply safe fixes.")
    check.add_argument(
        "--force-exclude",
        action="store_true",
        help="Apply excludes to files named directly.",
    )
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command.

    Args:
        argv: Command arguments. Use process arguments if None.

    Returns:
        The exit code.
    """
    parser = parse_args()
    args = parser.parse_args(argv)

    cmd = args.command

    if cmd is None:
        parser.print_help()
        return 0
    try:
        config = load_config(find_root(Path.cwd()))
        match cmd:
            case "init":
                init_project(
                    root=Path.cwd(),
                    skip_config=args.skip_config,
                    skip_pre_commit=args.skip_pre_commit,
                    skip_ci=args.skip_ci,
                    skip_hooks=args.skip_hooks,
                )
                return 0
            case "guard":
                guard_command(args.shell_command)
                return 0
            case "sync":
                sync_packages(config)
                return 0
        commit_msg = args.commit_msg
        if commit_msg is not None and (args.paths or args.fix or args.unsafe_fixes):
            raise ValueError("--commit-msg cannot use Markdown paths or fix flags.")
        baseline = Baseline() if args.write_baseline else load_baseline(config.root)
        if commit_msg is not None:
            with open(Path(commit_msg), encoding="utf-8", newline="") as f:
                msg = f.read()
            findings = check_message(text=msg, config=config)
        else:
            paths = [str(Path.cwd() / path) for path in (args.paths or ["."])]
            selected = select_files(
                paths=paths, config=config, force_exclude=args.force_exclude
            )
            if not selected:
                if not args.force_exclude:
                    print(
                        "slop_away: No Markdown files to check. An exclude, "
                        ".gitignore, or include setting skips every input.",
                        file=sys.stderr,
                    )
                if args.output_format == "json":
                    print("[]")
                return 0
            findings = (
                fix_files(paths=selected, config=config, unsafe=args.unsafe_fixes)
                if args.fix or args.unsafe_fixes
                else check_files(paths=selected, config=config)
            )
        if args.write_baseline:
            baseline = write_baseline(root=config.root, findings=findings)
        findings = [f for f in findings if not baseline.matches(f)]
        print(render_findings(findings, args.output_format), end="")
        return int(bool(findings))
    except (ConfigError, OSError, UnicodeError, ValueError) as e:
        print(f"slop_away: {e}", file=sys.stderr)
        return 2
    except Exception:
        logger.exception("Unexpected error")
        return 2
