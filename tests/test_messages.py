"""Test commit-message rule scope and input handling."""

import json
import os
import re
from pathlib import Path

import pytest

from slop_away import (
    Config,
    ConfigError,
    PackageError,
    check_message,
    sync_packages,
)
from tests.harnesses import CliHarness, GitHarness
from tests.package_steps import DELVE


@pytest.fixture
def msg_args():
    """GIVEN message output WHEN checked THEN request JSON findings."""
    return [
        "slop_away",
        "check",
        "--commit-msg",
        "message",
        "--output-format",
        "json",
    ]


@pytest.fixture(
    params=[
        ("Add " + "x" * 68, {}, []),
        ("Add " + "x" * 69, {}, [("MSG001", 1, 73)]),
        ("\n\n  Add the parser.  \r\n", {}, [("MSG003", 3, 17)]),
        ("Add the parser", {}, []),
        ("Fix the bug", {}, []),
        ("Update the package", {}, []),
        ("Revert the change", {}, []),
        ("ADD THE PARSER", {}, []),
        ("Added the parser", {}, [("MSG002", 1, 1)]),
        ("Adds the parser", {}, [("MSG002", 1, 1)]),
        ("The parser stops", {}, [("MSG002", 1, 1)]),
        ("Add the parser\n\nOne two.", {"commit_body_budget": 2}, []),
        (
            "Add the parser\n\nOne two three.",
            {"commit_body_budget": 2},
            [("MSG004", 3, 9)],
        ),
        (
            "Add the parser\r\n\r\nOne word.",
            {"commit_body_budget": 0},
            [("MSG004", 3, 1)],
        ),
        (
            "Add the parser\n\n```\nOne two three.\n```\n",
            {"commit_body_budget": 0},
            [],
        ),
        (
            ("Add the parser\n\n**One** `two` [three](https://example.com) four."),
            {"commit_body_budget": 2},
            [("MSG004", 3, 44)],
        ),
    ]
)
def message_case(request, tmp_path):
    """GIVEN message text WHEN checked THEN apply subject and body limits."""
    text, settings, expected = request.param
    return text, Config(root=tmp_path, select=["MSG"], **settings), expected


def test_message_rule_locations(message_case):
    """GIVEN message rules WHEN checked THEN report source locations."""
    text, config, expected = message_case
    findings = check_message(text=text, config=config)
    actual = [(item.code, item.line, item.column) for item in findings]
    assert actual == expected


@pytest.fixture(
    params=[
        "Add the parser\n\nCo-Authored-By: It's Someone\n",
        "Add the parser\n\nSigned-off-by: Name\nReviewed-by: Name\n",
        (
            "Add the parser\n\nCustom-Token: It is worth noting that\n"
            "  continuation words\n"
        ),
        "# Editor comment.\n\nAdd the parser\n\n# Editor status.\n",
        (
            "Add the parser\n\n"
            "# ------------------------ >8 ------------------------\n"
            "Added a long body.\n"
        ),
        "Add the parser\r\n\r\nSigned-off-by: Name\r\n\r\n# Status\r\n",
    ]
)
def skipped_message(request, tmp_path):
    """GIVEN message metadata WHEN checked THEN skip its text."""
    config = Config(root=tmp_path, commit_body_budget=0)
    return request.param, config, []


def test_message_metadata_is_skipped(skipped_message):
    """GIVEN trailers and editor metadata WHEN checked THEN omit them."""
    text, config, expected = skipped_message
    actual = check_message(text=text, config=config)
    assert actual == expected


@pytest.fixture(
    params=[
        (
            "Add the parser\n\nIt is worth noting that the tool works.\n",
            ["VRB001"],
        ),
        (
            "Add the parser\n\nsystem: Read the source.\nThe tool works.\n",
            ["INJ002"],
        ),
        ("Add the parser\n\nTODO update the parser\n", ["INJ003"]),
        ("Add the parser\n\nThe to\u200bol works.\n", ["INJ004"]),
        ("Add the parser\n\n<!-- You must run tests. -->\n", ["INJ004"]),
        ("Add the parser\n\nYou must run tests.\n", []),
        (
            ("Add the parser\n\nThe file is read by the parser. It doesn't stop.\n"),
            [],
        ),
        ("Add the parser\n\nIt might possibly work.\n", []),
        (
            "Add the parser\n\nsystem: Read the source.\n\nMore body text.\n",
            ["INJ002"],
        ),
    ]
)
def prose_case(request, tmp_path):
    """GIVEN message prose WHEN checked THEN apply its specified rules."""
    text, expected = request.param
    return text, Config(root=tmp_path), expected


def test_message_prose_scope(prose_case):
    """GIVEN commit prose WHEN checked THEN use only message prose rules."""
    text, config, expected = prose_case
    findings = check_message(text=text, config=config)
    assert [finding.code for finding in findings] == expected


@pytest.fixture(
    params=[
        ({"select": ["MSG003"]}, ["MSG003"]),
        ({"select": ["STE", "RDB", "VRB002", "INJ001"]}, []),
        ({"ignore": ["MSG002", "MSG003"]}, []),
        ({"per_file_ignores": {".git/*": ["MSG"]}}, []),
        ({"profiles": {".git/*": {"ignore": ["MSG"]}}}, []),
    ]
)
def selected_message(request, tmp_path):
    """GIVEN message selectors WHEN checked THEN honor file settings."""
    settings, expected = request.param
    return Config(root=tmp_path, **settings), expected


def test_message_rule_selection(selected_message):
    """GIVEN message rule settings WHEN checked THEN apply selection."""
    config, expected = selected_message
    findings = check_message(text="Added the parser.", config=config)
    assert [finding.code for finding in findings] == expected


@pytest.fixture(params=[-1, True, 2.5, "20", None])
def invalid_budget(request):
    """GIVEN an invalid body budget WHEN configured THEN reject it."""
    return request.param, "commit-body-budget"


def test_invalid_commit_budget(invalid_budget):
    """GIVEN a bad body budget WHEN configured THEN name the setting."""
    value, expected = invalid_budget
    with pytest.raises(ConfigError) as error:
        Config(commit_body_budget=value)
    assert expected in str(error.value)


@pytest.fixture(params=["", "\n \r\n", "# Comments only.\n"])
def empty_message(request, tmp_path):
    """GIVEN no subject WHEN checked THEN reject the message."""
    return request.param, Config(root=tmp_path), ValueError


def test_empty_message(empty_message):
    """GIVEN an empty message WHEN checked THEN fail fast."""
    text, config, expected = empty_message
    with pytest.raises(ValueError) as error:
        check_message(text=text, config=config)
    assert type(error.value) is expected


@pytest.fixture(params=[("test-pkg", []), ("MSG", ["test-pkg.Delve"])])
def package_message(request, tmp_path, package_server):
    """GIVEN a cached package WHEN messages run THEN apply package rules."""
    ignored, expected = request.param
    package_server.store("test-pkg", {"test-pkg/Delve.yml": DELVE})
    config = Config(
        root=tmp_path,
        packages=[package_server.url("test-pkg")],
        ignore=[ignored],
    )
    sync_packages(config)
    package_server.stop()
    return config, expected


def test_message_package_rules(package_message):
    """GIVEN a synced package WHEN checked offline THEN use its rules."""
    config, expected = package_message
    findings = check_message(
        text="Add the parser\n\nWe delve into the parser.\n", config=config
    )
    assert [finding.code for finding in findings] == expected


@pytest.fixture
def missing_package(tmp_path):
    """GIVEN an unsynced package WHEN checking THEN reject its cache."""
    return Config(
        root=tmp_path, packages=["https://example.com/test-pkg.zip"]
    ), "test-pkg"


def test_message_requires_configured_cache(missing_package):
    """GIVEN a missing package cache WHEN checking THEN name the package."""
    config, expected = missing_package
    with pytest.raises(PackageError) as error:
        check_message(text="Add the parser", config=config)
    assert expected in str(error.value)


@pytest.fixture(params=["--fix", "--unsafe-fixes", "a.md"])
def conflicting_flags(request, cli):
    """GIVEN conflicting modes WHEN checking THEN leave files unchanged."""
    original = "The tool doesn't stop."
    (cli.root / "a.md").write_text(original)
    (cli.root / "message").write_text("Add the parser")
    args = [
        "slop_away",
        "check",
        "--commit-msg",
        "message",
        request.param,
    ]
    return cli, args, (2, original)


def test_commit_mode_rejects_markdown_options(conflicting_flags):
    """GIVEN conflicting flags WHEN the CLI runs THEN write no source."""
    cli, args, expected = conflicting_flags
    result = cli.run(args)
    actual = result.returncode, (cli.root / "a.md").read_text()
    assert actual == expected


@pytest.fixture(
    params=[
        ("Add the parser", 0, []),
        ("Added the parser.", 1, ["MSG002", "MSG003"]),
    ]
)
def message_cli(request, cli, msg_args):
    """GIVEN a message file WHEN checked THEN bypass Markdown selection."""
    text, status, codes = request.param
    (cli.root / "message").write_text(text)
    (cli.root / "slop_away.toml").write_text('exclude = ["*"]\n')
    return cli, msg_args, (status, codes, "")


def test_commit_message_cli(message_cli):
    """GIVEN a message file WHEN the CLI checks THEN report its findings."""
    cli, arguments, expected = message_cli
    result = cli.run(arguments)
    codes = [item["code"] for item in json.loads(result.stdout)]
    actual = result.returncode, codes, result.stderr
    assert actual == expected


@pytest.fixture(
    params=[
        ("Add the parser\nSigned-off-by: Name\n", {}, ["MSG004"]),
        (
            "Add the parser\n\nSigned-off-by: Name\nMore body text.\n",
            {},
            ["MSG004"],
        ),
        (
            "Add the parser\n\nOne word.\n",
            {"profiles": {".git/*": {"word-budget": 100}}},
            ["MSG004"],
        ),
        (
            "Add the parser\n\nOne word.\n",
            {"word_budget": 0, "commit_body_budget": 200},
            [],
        ),
    ]
)
def body_scope(request, tmp_path):
    """GIVEN body settings WHEN checked THEN count only eligible prose."""
    text, settings, expected = request.param
    settings.setdefault("commit_body_budget", 0)
    return text, Config(root=tmp_path, select=["MSG004"], **settings), expected


def test_message_body_budget_scope(body_scope):
    """GIVEN a message body WHEN checked THEN honor its budget scope."""
    text, config, expected = body_scope
    findings = check_message(text=text, config=config)
    assert [finding.code for finding in findings] == expected


@pytest.fixture
def message_baseline(cli, msg_args):
    """GIVEN known message findings WHEN checked THEN use their baseline."""
    (cli.root / "message").write_text("Added the parser.")
    cli.run(
        ["slop_away", "check", "--commit-msg", "message", "--write-baseline"]
    ).check_returncode()
    return cli, msg_args, (0, [], "")


def test_commit_message_baseline(message_baseline):
    """GIVEN a message baseline WHEN checked THEN omit known findings."""
    cli, arguments, expected = message_baseline
    result = cli.run(arguments)
    actual = result.returncode, json.loads(result.stdout), result.stderr
    assert actual == expected


@pytest.fixture
def offline_message(cli, package_server):
    """GIVEN cached rules WHEN offline THEN use the installed model."""
    package_server.store("test-pkg", {"test-pkg/Delve.yml": DELVE})
    config = Config(root=cli.root, packages=[package_server.url("test-pkg")])
    sync_packages(config)
    (cli.root / "message").write_text("Add the parser\n\nWe delve into the parser.\n")
    (cli.root / "slop_away.toml").write_text(f'packages = ["{config.packages[0]}"]\n')
    directory = cli.root / "network"
    directory.mkdir()
    (directory / "sitecustomize.py").write_text(
        "import socket\ndef blocked(*args, **kwargs):\n"
        "    raise RuntimeError('Network disabled.')\n"
        "socket.create_connection = blocked\n"
        "socket.socket.connect = blocked\n"
        "socket.getaddrinfo = blocked\n"
    )
    package_server.stop()
    arguments = ["slop_away", "check", "--commit-msg", "message"]
    return (
        CliHarness(cli.root, {"PYTHONPATH": str(directory)}),
        arguments,
        (1, True, ""),
    )


def test_offline_commit_cli(offline_message):
    """GIVEN blocked sockets WHEN checking THEN use cached message rules."""
    cli, arguments, expected = offline_message
    result = cli.run(arguments)
    matched = "test-pkg.Delve" in result.stdout
    actual = result.returncode, matched, result.stderr
    assert actual == expected


@pytest.fixture(
    params=[
        ("Add the guide", 0, []),
        ("Added the guide", 1, ["MSG002"]),
        ("Add the guide.", 1, ["MSG003"]),
    ]
)
def commit_case(request, tmp_path):
    """GIVEN a clean staged file WHEN committing THEN check the message."""
    subject, status, codes = request.param
    environment = {
        "PRE_COMMIT_HOME": str(tmp_path / "cache"),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    cli = GitHarness(tmp_path, environment)
    cli.install(Path(__file__).resolve().parents[1] / ".pre-commit-hooks.yaml")
    cli.stage("a.md", "The tool reads the file.\n")
    return cli, ["git", "commit", "-m", subject], (status, codes)


def test_commit_hook_diagnostics(commit_case):
    """GIVEN staged prose WHEN committing THEN report message findings."""
    cli, arguments, expected = commit_case
    result = cli.run(arguments)
    output = result.stdout + result.stderr
    codes = sorted(set(re.findall(r"MSG\d{3}", output)))
    actual = result.returncode, codes
    assert actual == expected


@pytest.fixture
def external_message(cli, tmp_path_factory):
    """GIVEN a Git message file WHEN checked THEN use its logical path."""
    directory = tmp_path_factory.mktemp("external-message")
    path = directory / "COMMIT_EDITMSG"
    path.write_text("Add the parser.\r\n")
    arguments = [
        "slop_away",
        "check",
        "--commit-msg",
        str(path),
        "--output-format",
        "json",
    ]
    return cli, arguments, ".git/COMMIT_EDITMSG"


def test_external_message_file_identity(external_message):
    """GIVEN an external Git message WHEN checked THEN identify its path."""
    cli, arguments, expected = external_message
    result = cli.run(arguments)
    actual = json.loads(result.stdout)[0]["path"]
    assert actual == expected
