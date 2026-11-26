"""Check literal shell commands for skipped commit hooks."""

import re
import shlex
from collections.abc import Iterator
from pathlib import PurePosixPath

MAX_CMD_DEPTH = 4

SHELL_RESERVED_WORDS = {
    "if",
    "then",
    "else",
    "elif",
    "do",
    "while",
    "until",
    "!",
}

COMMIT_ARGS = {
    "--message",
    "--file",
    "--template",
    "--reedit-message",
    "--reuse-message",
    "--author",
    "--date",
    "--cleanup",
    "--pathspec-from-file",
    "--trailer",
    "--fixup",
    "--squash",
}

ENV_OPTIONS = {"-u", "--unset", "-C", "--chdir"}

SHELL_CMDS = {"env", "command", "exec"}

SHELL_BINARIES = {"bash", "sh", "dash", "zsh"}

SHELL_OPTIONS = {
    "-c",
    "-C",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--config-env",
}


def _segments(cmd: str) -> Iterator[list[str]]:
    """Read shell command segments.

    Args:
        cmd: The shell source.

    Yields:
        Literal argument lists.

    Raises:
        ValueError: A quote or escape is incomplete.
    """
    buffer: list[str] = []
    quote = ""
    escaped = False
    comment = False
    for char in cmd:
        if comment:
            if char != "\n":
                continue
            comment = False
        if escaped:
            if char == "\n":
                buffer.pop()
            else:
                buffer.append(char)
            escaped = False
        elif char == "\\" and quote != "'":
            buffer.append(char)
            escaped = True
        elif quote:
            buffer.append(char)
            if char == quote:
                quote = ""
        elif char in "\"'":
            buffer.append(char)
            quote = char
        elif char == "#" and (not buffer or buffer[-1].isspace()):
            comment = True
        elif char in ";|&()\n":
            yield shlex.split("".join(buffer))
            buffer = []
        else:
            buffer.append(char)
    if quote or escaped:
        raise ValueError("Shell command has an incomplete quote or escape.")
    yield shlex.split("".join(buffer))


def _commit(args: list[str]) -> bool:
    """Check commit arguments.

    Args:
        args: The arguments after the commit subcommand.

    Returns:
        True if a hook skip option is present.
    """

    idx = 0
    while idx < len(args):
        value = args[idx]
        idx += 1
        if value == "--":
            return False
        if value == "--no-verify" or value.startswith("--no-verify="):
            return True
        if value in COMMIT_ARGS:
            idx += 1
        elif value.startswith("-") and not value.startswith("--"):
            for offset, option in enumerate(value[1:], 1):
                if option == "n":
                    return True
                if option in "mFtcC":
                    idx += int(offset == len(value) - 1)
                    break
                if option == "S":
                    break
    return False


def _inspect(args: list[str], depth: int) -> bool:
    """Check a literal command invocation.

    Args:
        args: The command arguments.
        depth: The number of nested shell commands.

    Returns:
        True if the invocation skips commit hooks.

    Raises:
        ValueError: Shell nesting exceeds the limit.
    """
    if depth > MAX_CMD_DEPTH:
        raise ValueError(
            f"Shell command exceeds {MAX_CMD_DEPTH} nested command strings."
        )
    idx = 0
    while idx < len(args):
        word = args[idx]
        name = PurePosixPath(word).name
        if re.match(r"[A-Za-z_][A-Za-z0-9_]*=", word) or word in SHELL_RESERVED_WORDS:
            idx += 1
        elif name in SHELL_CMDS:
            idx += 1
            while idx < len(args) and args[idx].startswith("-"):
                option = args[idx]
                idx += 2 if option in ENV_OPTIONS else 1
        else:
            break
    if idx >= len(args):
        return False
    name = PurePosixPath(args[idx]).name
    rest = args[idx + 1 :]
    if name in SHELL_BINARIES:
        for offset, option in enumerate(rest):
            if (
                option.startswith("-")
                and not option.startswith("--")
                and "c" in option[1:]
                and offset + 1 < len(rest)
            ):
                return any(
                    _inspect(segment, depth + 1)
                    for segment in _segments(rest[offset + 1])
                )
        return False
    if name != "git":
        return False
    idx = 0
    while idx < len(rest) and rest[idx].startswith("-"):
        option = rest[idx]
        idx += 2 if option in SHELL_OPTIONS else 1
    return idx < len(rest) and rest[idx] == "commit" and _commit(rest[idx + 1 :])


def guard_command(cmd: str) -> None:
    """Reject literal commands that skip commit hooks.

    Args:
        cmd: The shell command to inspect.

    Raises:
        TypeError: The command is not text.
        ValueError: The command is empty, invalid, or skips commit hooks.
    """
    if not cmd.strip() or "\x00" in cmd:
        raise ValueError(f"Expected a nonempty shell command without NUL. got '{cmd}'.")
    for seg in _segments(cmd):
        if _inspect(seg, 0):
            raise ValueError("Commit hooks must run. Remove --no-verify or -n.")
