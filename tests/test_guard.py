"""Test literal shell command checks."""

import pytest

from slop_away import guard_command


@pytest.fixture(
    params=[
        "git commit --no-verify -m wip",
        "git commit -n -m wip",
        "git commit -an -m wip",
        "git -C 'a b' commit -n",
        "git -c user.name=Test commit --no-verify",
        "/usr/bin/git commit '-n'",
        "env FOO=bar git commit -n",
        "command git commit -n",
        "echo ok && git commit -n",
        "if git commit -n; then echo ok; fi",
        "git status;git commit -n",
        "bash -lc 'git commit -n -m wip'",
        "git commit -m ';' -n",
        "git \\\ncommit --no-verify",
        'git comm""it --no-verify',
    ]
)
def blocked_command(request):
    """GIVEN a hook skip command WHEN checked THEN reject it."""
    return request.param, ValueError


def test_guard_blocks_skipped_hooks(blocked_command):
    """GIVEN skip flags WHEN checked THEN reject the command."""
    command, expected = blocked_command
    with pytest.raises(ValueError) as error:
        guard_command(command)
    assert type(error.value) is expected


@pytest.fixture(
    params=[
        "git commit -m wip",
        "git commit -m 'git commit --no-verify'",
        "git commit -m '--no-verify'",
        "git commit --message=-n",
        "git commit -- --no-verify",
        "git commit -Sname -m wip",
        "git commit -am 'text -n'",
        "git status",
        "echo 'git commit -n'",
        "printf '%s' ';' git commit -n",
        "echo ok # git commit -n",
        "git commit --author '-n' -m wip",
        "git config user.name Test",
    ]
)
def allowed_command(request):
    """GIVEN ordinary shell input WHEN checked THEN leave it unchanged."""
    return request.param, None


def test_guard_allows_normal_commands(allowed_command):
    """GIVEN normal commands WHEN checked THEN permit the command."""
    command, expected = allowed_command
    actual = guard_command(command)
    assert actual is expected


@pytest.fixture(
    params=["", " ", "git commit 'unterminated", "git commit \\", "x\x00y"]
)
def invalid_command(request):
    """GIVEN invalid shell input WHEN checked THEN reject it."""
    return request.param, ValueError


def test_guard_rejects_invalid_input(invalid_command):
    """GIVEN invalid command text WHEN checked THEN fail fast."""
    command, expected = invalid_command
    with pytest.raises(ValueError) as error:
        guard_command(command)
    assert type(error.value) is expected


@pytest.fixture
def harmless_command(tmp_path):
    """GIVEN a command string WHEN checked THEN do not execute it."""
    path = tmp_path / "marker"
    return f"touch {path}", path


def test_guard_does_not_execute_input(harmless_command):
    """GIVEN executable text WHEN inspected THEN create no command output."""
    command, path = harmless_command
    guard_command(command)
    assert not path.exists()
