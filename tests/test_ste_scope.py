"""Test rule selection and offline STE checks."""

import pytest

from slop_away import Config, check_text
from tests.harnesses import CliHarness


@pytest.fixture(
    params=[
        ("AGENTS.md", {}, []),
        ("skills/a/SKILL.md", {}, []),
        ("docs/a.md", {"select": ["INJ"]}, []),
        ("docs/a.md", {"ignore": ["STE004"]}, []),
        ("docs/a.md", {"select": ["STE004"]}, ["STE004"]),
        (
            "docs/a.md",
            {
                "select": ["STE004"],
                "profiles": {"docs/**/*.md": {"ignore": ["STE"]}},
            },
            [],
        ),
    ]
)
def scope_case(request):
    """GIVEN rule settings WHEN checked THEN apply STE only where selected."""
    path, settings, expected = request.param
    return "The tool doesn't run twice.", path, Config(**settings), expected


def test_ste_scope(scope_case):
    """GIVEN rule settings WHEN checked THEN honor the STE scope."""
    text, path, config, expected = scope_case
    findings = check_text(text, path, config)
    actual = [finding.code for finding in findings]
    assert actual == expected


@pytest.fixture
def offline_case(cli):
    """GIVEN no network WHEN the CLI starts THEN use the installed model."""
    directory = cli.root / "network"
    directory.mkdir()
    source = (
        "import socket\n"
        "def blocked(*args, **kwargs):\n"
        "    raise RuntimeError('Network access is disabled in this test.')\n"
        "socket.create_connection = blocked\n"
        "socket.socket.connect = blocked\n"
        "socket.socket.connect_ex = blocked\n"
        "socket.getaddrinfo = blocked\n"
    )
    (directory / "sitecustomize.py").write_text(source, encoding="utf-8")
    (cli.root / "slop_away.toml").write_text(
        'select = ["STE003"]', encoding="utf-8"
    )
    (cli.root / "a.md").write_text(
        "The file is read by the parser.", encoding="utf-8"
    )
    harness = CliHarness(cli.root, {"PYTHONPATH": str(directory)})
    return harness, ["slop_away", "check", "a.md"], "STE003", (1, True, "")


def test_offline_model(offline_case):
    """GIVEN no network WHEN the CLI checks prose THEN return STE findings."""
    cli, arguments, code, expected = offline_case
    result = cli.run(arguments)
    actual = result.returncode, code in result.stdout, result.stderr
    assert actual == expected
