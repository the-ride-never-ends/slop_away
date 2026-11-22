"""Supply the slop_away command."""

from argparse import ArgumentParser
from collections.abc import Sequence
from importlib.metadata import version


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
    parser.parse_args(argv)
    parser.print_help()
    return 0
