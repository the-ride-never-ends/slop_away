"""Check literal shell commands for skipped commit hooks."""

import re
import shlex
from collections.abc import Iterator
from pathlib import PurePosixPath


def _segments(command: str) -> Iterator[list[str]]:
    """Read shell command segments.

    Args:
        command: The shell source.

    Yields:
        Literal argument lists.

    Raises:
        ValueError: A quote or escape is incomplete.
    """
    buffer: list[str] = []
    quote = ""
    escaped = False
    comment = False
    for char in command:
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


def _commit(arguments: list[str]) -> bool:
    """Check commit arguments.

    Args:
        arguments: The arguments after the commit subcommand.

    Returns:
        True if a hook skip option is present.
    """
    values = {
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
    index = 0
    while index < len(arguments):
        value = arguments[index]
        index += 1
        if value == "--":
            return False
        if value == "--no-verify" or value.startswith("--no-verify="):
            return True
        if value in values:
            index += 1
        elif value.startswith("-") and not value.startswith("--"):
            for offset, option in enumerate(value[1:], 1):
                if option == "n":
                    return True
                if option in "mFtcC":
                    index += int(offset == len(value) - 1)
                    break
                if option == "S":
                    break
    return False


def _inspect(arguments: list[str], depth: int) -> bool:
    """Check a literal command invocation.

    Args:
        arguments: The command arguments.
        depth: The number of nested shell commands.

    Returns:
        True if the invocation skips commit hooks.

    Raises:
        ValueError: Shell nesting exceeds the limit.
    """
    if depth > 4:
        raise ValueError("Shell command exceeds four nested command strings.")
    index = 0
    while index < len(arguments):
        word = arguments[index]
        name = PurePosixPath(word).name
        if re.match(r"[A-Za-z_][A-Za-z0-9_]*=", word) or word in {
            "if",
            "then",
            "else",
            "elif",
            "do",
            "while",
            "until",
            "!",
        }:
            index += 1
        elif name in {"env", "command", "exec"}:
            index += 1
            while index < len(arguments) and arguments[index].startswith("-"):
                option = arguments[index]
                index += (
                    2 if option in {"-u", "--unset", "-C", "--chdir"} else 1
                )
        else:
            break
    if index >= len(arguments):
        return False
    name = PurePosixPath(arguments[index]).name
    rest = arguments[index + 1 :]
    if name in {"bash", "sh", "dash", "zsh"}:
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
    index = 0
    while index < len(rest) and rest[index].startswith("-"):
        option = rest[index]
        index += (
            2
            if option
            in {
                "-c",
                "-C",
                "--git-dir",
                "--work-tree",
                "--namespace",
                "--config-env",
            }
            else 1
        )
    return (
        index < len(rest)
        and rest[index] == "commit"
        and _commit(rest[index + 1 :])
    )


def guard_command(command: str) -> None:
    """Reject literal commands that skip commit hooks.

    Args:
        command: The shell command to inspect.

    Raises:
        TypeError: The command is not text.
        ValueError: The command is empty, invalid, or skips commit hooks.
    """
    if not isinstance(command, str):
        raise TypeError("Expected shell command text.")
    if not command.strip() or "\x00" in command:
        raise ValueError("Expected a nonempty shell command without NUL.")
    for segment in _segments(command):
        if _inspect(segment, 0):
            raise ValueError(
                "Commit hooks must run; remove --no-verify or -n."
            )
