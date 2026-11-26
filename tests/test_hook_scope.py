"""Test hook event boundaries and command arguments."""

import json

import pytest

from slop_away import init_project
from tests.harnesses import HookHarness


@pytest.fixture(
    params=[
        ("post_edit", "invalid"),
        ("pre_bash", "{}"),
        ("stop", "{}"),
        (
            "post_edit",
            '{"hook_event_name":"PostToolUse","tool_name":"Write","cwd":1,"tool_input":{"file_path":"a.md"}}',
        ),
        ("stop", '{"hook_event_name":"Stop","stop_hook_active":"true"}'),
        (
            "pre_bash",
            '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":null}}',
        ),
    ]
)
def invalid_event(request, hook_cli):
    """GIVEN malformed input WHEN a hook runs THEN block the event."""
    script, source = request.param
    path = hook_cli.root / ".claude/hooks" / f"slop_away_{script}.sh"
    return hook_cli, ["bash", str(path)], source, 2


def test_hooks_reject_malformed_events(invalid_event):
    """GIVEN bad event data WHEN a hook runs THEN return a blocking code."""
    cli, arguments, source, expected = invalid_event
    result = cli.run(arguments, source)
    assert result.returncode == expected


@pytest.fixture
def quoted_path(hook_cli):
    """GIVEN shell characters in a path WHEN checked THEN keep them literal."""
    name = "a b;$(touch marker).md"
    (hook_cli.root / name).write_text("You must run the tests first.")
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "cwd": str(hook_cli.root),
        "tool_input": {"file_path": name},
    }
    return hook_cli, payload, (2, True, False)


def test_post_edit_keeps_file_paths_literal(quoted_path):
    """GIVEN a quoted path WHEN its hook runs THEN execute no path data."""
    cli, payload, expected = quoted_path
    result = cli.event("post_edit", payload)
    created = (cli.root / "marker").exists()
    actual = result.returncode, "INJ001" in result.stderr, created
    assert actual == expected


@pytest.fixture
def nested_edit(hook_cli):
    """GIVEN a nested event cwd WHEN checked THEN resolve its relative path."""
    directory = hook_cli.root / "docs"
    directory.mkdir()
    (directory / "a.md").write_text("You must run the tests first.")
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "cwd": str(directory),
        "tool_input": {"file_path": "a.md"},
    }
    return hook_cli, payload, (2, True)


def test_post_edit_uses_event_cwd(nested_edit):
    """GIVEN a relative edited path WHEN checked THEN use the event cwd."""
    cli, payload, expected = nested_edit
    result = cli.event("post_edit", payload)
    actual = result.returncode, "docs/a.md" in result.stderr
    assert actual == expected


@pytest.fixture
def unavailable_cache(hook_cli):
    """GIVEN an unavailable package WHEN a hook checks THEN report it."""
    (hook_cli.root / "slop_away.toml").write_text(
        'packages = ["https://example.com/missing.zip"]\n'
    )
    (hook_cli.root / "a.md").write_text("The tool reads the file.")
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "cwd": str(hook_cli.root),
        "tool_input": {"file_path": "a.md"},
    }
    return hook_cli, payload, (2, True)


def test_post_edit_reports_check_errors(unavailable_cache):
    """GIVEN a check error WHEN the hook runs THEN block with feedback."""
    cli, payload, expected = unavailable_cache
    result = cli.event("post_edit", payload)
    actual = result.returncode, "missing" in result.stderr
    assert actual == expected


@pytest.fixture
def active_stop(hook_cli):
    """GIVEN a second stop pass WHEN the config is bad THEN permit stopping."""
    (hook_cli.root / "slop_away.toml").write_text("invalid = 1\n")
    return (
        hook_cli,
        {"hook_event_name": "Stop", "stop_hook_active": True},
        (0, "", ""),
    )


def test_active_stop_does_not_repeat_checks(active_stop):
    """GIVEN an active stop hook WHEN called again THEN permit stopping."""
    cli, payload, expected = active_stop
    result = cli.event("stop", payload)
    actual = result.returncode, result.stdout, result.stderr
    assert actual == expected


@pytest.fixture
def settings_command(tmp_path):
    """GIVEN a path with spaces WHEN its settings run THEN find hooks."""
    root = tmp_path / "project with spaces"
    root.mkdir()
    init_project(root=root)
    (root / "a.md").write_text("The tool reads the file.")
    settings = json.loads((root / ".claude/settings.json").read_text())
    command = settings["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "cwd": str(root),
        "tool_input": {"file_path": "a.md"},
    }
    cli = HookHarness(root, {"CLAUDE_PROJECT_DIR": str(root)})
    return cli, ["bash", "-c", command], json.dumps(payload), (0, "", "")


def test_generated_settings_quote_project_paths(settings_command):
    """GIVEN generated settings WHEN run THEN quote the project path."""
    cli, arguments, source, expected = settings_command
    result = cli.run(arguments, source)
    actual = result.returncode, result.stdout, result.stderr
    assert actual == expected
