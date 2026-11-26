"""Test fix scope and source preservation."""

import pytest

from slop_away import Config, apply_fixes, fix_files, sync_packages


@pytest.fixture(
    params=[
        ("The tool doesn't run twice.", "The tool does not run twice."),
        ("The tool doesn’t run twice.", "The tool does not run twice."),
        ("Don't stop. CAN'T STOP.", "Do not stop. CANNOT STOP."),
        (
            "I'm ready. We're ready. They've stopped.",
            "I am ready. We are ready. They have stopped.",
        ),
        ("I'll stop. Let's stop.", "I will stop. Let us stop."),
        (
            "It's ready. He's stopped. I'd stop.",
            "It's ready. He's stopped. I'd stop.",
        ),
        ("The parser's state stays valid.", "The parser's state stays valid."),
        (
            "#   The tool\n\nThe tool runs.   Then stops.  \nNext line.\n",
            "# The tool\n\nThe tool runs. Then stops.  \nNext line.\n",
        ),
        (
            "The tool runs.\r\nIt doesn't stop.\r\n",
            "The tool runs.\r\nIt does not stop.\r\n",
        ),
        (
            "- The tool doesn't stop.\n  - It  works.",
            "- The tool does not stop.\n  - It works.",
        ),
        ("**Don't** stop.", "**Do not** stop."),
        ("The tool does&#110;'t stop.", "The tool does&#110;'t stop."),
        ("The to\u200bol doesn't stop.", "The tool does not stop."),
        ("The \u202etool\u202c runs.", "The tool runs."),
        (
            "Emoji: 👩\u200d💻; text: a\u200cb.",
            "Emoji: 👩\u200d💻; text: a\u200cb.",
        ),
        ("<!-- You must stop. a\u200bb -->", "<!-- You must stop. ab -->"),
        (
            "\u200b```\nThe tool doesn't stop.\n```\n",
            "```\nThe tool doesn't stop.\n```\n",
        ),
    ]
)
def safe_case(request, tmp_path):
    """GIVEN prose WHEN safe fixes run THEN preserve its meaning."""
    before, expected = request.param
    return before, "a.md", Config(root=tmp_path), False, expected


def test_safe_fix_behavior(safe_case):
    """GIVEN prose WHEN safe fixes run THEN return the expected source."""
    text, path, config, unsafe, expected = safe_case
    actual = apply_fixes(text=text, path=path, config=config, unsafe=unsafe)
    assert actual == expected


@pytest.fixture
def fixed_case(safe_case):
    """GIVEN a safe fix WHEN a second pass runs THEN use fixed source."""
    text, path, config, unsafe, _expected = safe_case
    fixed = apply_fixes(text=text, path=path, config=config, unsafe=unsafe)
    return fixed, path, config, unsafe


def test_safe_fixes_are_idempotent(fixed_case):
    """GIVEN fixed text WHEN fixed again THEN preserve the source."""
    expected, path, config, unsafe = fixed_case
    actual = apply_fixes(text=expected, path=path, config=config, unsafe=unsafe)
    assert actual == expected


@pytest.fixture(
    params=[
        "---\ntitle: Doesn't  stop.\n---\n",
        "```python\n# Doesn't  stop.\n```\n",
        "    Doesn't  stop.\n",
        "The `doesn't  stop` example.",
        "| Doesn't | stop |\n| --- | --- |\n| a | b |\n",
        "[The tool](https://example.com/doesn't)\n",
        '<span title="doesn\'t  stop">The tool runs.</span>',
        "<!-- The tool doesn't  stop. -->",
    ]
)
def excluded_case(request, tmp_path):
    """GIVEN skipped content WHEN fixed THEN preserve the source."""
    return request.param, Config(root=tmp_path), request.param


def test_fix_preserves_skipped_content(excluded_case):
    """GIVEN skipped Markdown WHEN fixed THEN leave its contents intact."""
    text, config, expected = excluded_case
    actual = apply_fixes(text=text, path="a.md", config=config, unsafe=True)
    assert actual == expected


@pytest.fixture(
    params=[
        (
            {"select": ["INJ"]},
            "a.md",
            "The tool doesn't stop. a\u200bb",
            "The tool doesn't stop. ab",
        ),
        (
            {"ignore": ["STE004", "INJ004"]},
            "a.md",
            "The tool doesn't stop. a\u200bb",
            "The tool doesn't stop. a\u200bb",
        ),
        (
            {"profiles": {"docs/*.md": {"ignore": ["STE004"]}}},
            "docs/a.md",
            "The tool doesn't stop.",
            "The tool doesn't stop.",
        ),
        (
            {},
            "AGENTS.md",
            "The tool doesn't  stop. a\u200bb",
            "The tool doesn't  stop. ab",
        ),
        (
            {"select": []},
            "a.md",
            "The  tool doesn't stop.",
            "The tool doesn't stop.",
        ),
    ]
)
def selection_case(request, tmp_path):
    """GIVEN selectors WHEN fixes run THEN honor each rule scope."""
    settings, path, text, expected = request.param
    return text, path, Config(root=tmp_path, **settings), expected


def test_fix_selection(selection_case):
    """GIVEN rule selection WHEN fixed THEN apply only allowed fixes."""
    text, path, config, expected = selection_case
    actual = apply_fixes(text=text, path=path, config=config, unsafe=True)
    assert actual == expected


@pytest.fixture(
    params=[
        (
            "In order to run the tool, open a shell.",
            "To run the tool, open a shell.",
        ),
        (
            "In   order  to run the tool, open a shell.",
            "To run the tool, open a shell.",
        ),
        ("It is worth noting that the tool works.", "The tool works."),
        (
            "The tool runs. It is important to note that the parser stops.",
            "The tool runs. The parser stops.",
        ),
        ("We utilize the parser.", "We use the parser."),
        ("The file is read by the parser.", "The file is read by the parser."),
        ("You must run the tests.", "You must run the tests."),
        ("**In order** to run the tool.", "**In order** to run the tool."),
    ]
)
def unsafe_case(request, tmp_path):
    """GIVEN unsafe edits WHEN requested THEN use their replacements."""
    text, expected = request.param
    config = Config(root=tmp_path, glossary={"use": ["utilize"]})
    return text, config, expected


def test_unsafe_fix_behavior(unsafe_case):
    """GIVEN unsafe fixes WHEN requested THEN change supported phrases."""
    text, config, expected = unsafe_case
    actual = apply_fixes(text=text, path="a.md", config=config, unsafe=True)
    assert actual == expected


@pytest.fixture(params=[False, True])
def package_swap(request, tmp_path, package_server):
    """GIVEN a package swap WHEN fixed THEN require the unsafe option."""
    rule = b"extends: substitution\nmessage: Use %s.\nswap: {utilize: use}\n"
    package_server.store("test-pkg", {"test-pkg/Use.yml": rule})
    config = Config(
        root=tmp_path,
        packages=[package_server.url("test-pkg")],
        select=["test-pkg"],
    )
    sync_packages(config)
    expected = "We use the parser." if request.param else "We utilize the parser."
    return config, request.param, expected


def test_external_swap(package_swap):
    """GIVEN a cached swap WHEN fixed THEN require unsafe permission."""
    config, unsafe, expected = package_swap
    actual = apply_fixes(
        text="We utilize the parser.", path="a.md", config=config, unsafe=unsafe
    )
    assert actual == expected


@pytest.fixture(params=["overlap", "cycle"])
def conflicting_case(request, tmp_path, package_server):
    """GIVEN conflicting edits WHEN fixed THEN reject the plan."""
    if request.param == "overlap":
        settings = {"glossary": {"for": ["in order to"]}}
    else:
        rule = (
            b"extends: substitution\nmessage: Use %s.\n"
            b"ignorecase: true\nswap: {in: out, out: in}\n"
        )
        package_server.store("test-pkg", {"test-pkg/Swap.yml": rule})
        settings = {
            "packages": [package_server.url("test-pkg")],
            "select": ["test-pkg"],
        }
        sync_packages(Config(root=tmp_path, **settings))
    return {
        "text": "In order to run the tool.",
        "path": "a.md",
        "config": Config(root=tmp_path, **settings),
        "unsafe": True,
    }


def test_conflicting_fix_plan(conflicting_case):
    """GIVEN overlapping or cyclic fixes WHEN applied THEN fail fast."""
    with pytest.raises(ValueError) as error:
        apply_fixes(**conflicting_case)
    expected = ValueError
    assert type(error.value) is expected


@pytest.fixture
def unreadable_batch(tmp_path):
    """GIVEN one bad input WHEN fixing files THEN preserve earlier files."""
    original = b"The tool doesn't stop.\r\n"
    path = tmp_path / "a.md"
    path.write_bytes(original)
    (tmp_path / "z.md").write_bytes(b"\xff")
    return path, original, Config(root=tmp_path)


def test_fix_validates_batch_before_writes(unreadable_batch):
    """GIVEN invalid UTF-8 WHEN fixing a batch THEN write no files."""
    path, expected, config = unreadable_batch
    with pytest.raises(UnicodeError):
        fix_files(paths=[config.root], config=config)
    assert path.read_bytes() == expected


@pytest.fixture(
    params=[
        ("--fix", "The tool doesn't stop.", "The tool does not stop.", 0),
        (
            "--unsafe-fixes",
            "In order to run the tool, open a shell.",
            "To run the tool, open a shell.",
            0,
        ),
        (
            "--fix",
            "The file is read by the parser.",
            "The file is read by the parser.",
            1,
        ),
    ]
)
def cli_case(request, cli):
    """GIVEN fix flags WHEN the CLI runs THEN save and check the result."""
    option, text, changed, status = request.param
    target = cli.root / "a.md"
    target.write_bytes((text + "\r\n").encode())
    target.chmod(0o640)
    return cli, target, option, ((changed + "\r\n").encode(), status, 0o640)


def test_fix_cli_preserves_file_properties(cli_case):
    """GIVEN a file WHEN CLI fixes run THEN preserve mode and line ends."""
    cli, path, option, expected = cli_case
    result = cli.run(["slop_away", "check", "a.md", option])
    actual = path.read_bytes(), result.returncode, path.stat().st_mode & 0o777
    assert actual == expected
