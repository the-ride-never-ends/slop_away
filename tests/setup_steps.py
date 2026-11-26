"""Supply initializer and agent-hook feature steps."""

import pytest
from pytest_bdd import given, parsers, then, when

from slop_away import init_project
from tests.harnesses import HookHarness


@pytest.fixture
def hook_cli(cli):
    """GIVEN project hooks WHEN events run THEN use the test project."""
    init_project(root=cli.root, skip_config=True, skip_pre_commit=True, skip_ci=True)
    return HookHarness(cli.root, {"CLAUDE_PROJECT_DIR": str(cli.root)})


@given("an empty project directory")
def empty_project(tmp_path):
    """GIVEN a new project WHEN init runs THEN use its directory."""
    tmp_path.mkdir(exist_ok=True)


@then(parsers.parse('the file "{path}" does not exist'))
def absent_file(tmp_path, path):
    """GIVEN an omitted target WHEN init ends THEN leave the path absent."""
    assert not (tmp_path / path).exists()


@when(
    parsers.parse('the post-edit hook script runs with a {tool} event for "{path}"'),
    target_fixture="result",
)
def edited_hook(hook_cli, tool, path):
    """GIVEN an edited file WHEN its hook runs THEN check the file."""
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": tool,
        "cwd": str(hook_cli.root),
        "tool_input": {"file_path": path},
    }
    return hook_cli.event("post_edit", payload)


@when(
    parsers.parse("the stop hook script runs with stop_hook_active {active}"),
    target_fixture="result",
)
def stopped_hook(hook_cli, active):
    """GIVEN a stop event WHEN checked THEN enforce one check pass."""
    payload = {
        "hook_event_name": "Stop",
        "cwd": str(hook_cli.root),
        "stop_hook_active": active == "true",
    }
    return hook_cli.event("stop", payload)


@when(
    parsers.parse('the pre-bash hook script runs with the command "{command}"'),
    target_fixture="result",
)
def command_hook(hook_cli, command):
    """GIVEN a shell command WHEN its hook runs THEN check hook skip flags."""
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "cwd": str(hook_cli.root),
        "tool_input": {"command": command},
    }
    return hook_cli.event("pre_bash", payload)
