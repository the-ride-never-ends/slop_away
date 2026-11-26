"""Test the package sync and offline check contracts."""

import io
import json
from zipfile import ZipFile, ZipInfo

import pytest
import yaml  # type: ignore[import-untyped]

from slop_away import (
    Config,
    ConfigError,
    PackageError,
    check_files,
    check_text,
    sync_packages,
)
from tests.harnesses import CliHarness
from tests.package_steps import DELVE


@pytest.fixture(params=["test-pkg/", "styles/test-pkg/", "test-pkg/styles/test-pkg/"])
def layout_case(request, tmp_path, package_server):
    """GIVEN a supported layout WHEN synced THEN supply its rules."""
    package_server.store("test-pkg", {request.param + "Delve.yml": DELVE})
    config = Config(
        root=tmp_path,
        packages=[package_server.url("test-pkg")],
        select=["test-pkg"],
    )
    sync_packages(config)
    return config, ["test-pkg.Delve"]


def test_package_layout(layout_case):
    """GIVEN a cached layout WHEN checked THEN run its package rule."""
    config, expected = layout_case
    actual = check_text("We delve into the parser.", "a.md", config)
    assert [item.code for item in actual] == expected


@pytest.fixture(
    params=[
        {"../bad.yml": DELVE, "test-pkg/Delve.yml": DELVE},
        {"/bad.yml": DELVE, "test-pkg/Delve.yml": DELVE},
        {"bad\\path": DELVE, "test-pkg/Delve.yml": DELVE},
        {"elsewhere/Delve.yml": DELVE},
        {"test-pkg/Delve.yml": DELVE, "styles/test-pkg/Delve.yml": DELVE},
        {"test-pkg/Delve.yml": DELVE, "test-pkg/nested/Other.yml": DELVE},
        {"test-pkg/Delve.yml": DELVE, "test-pkg/Delve.yaml": DELVE},
        {"test-pkg/1Invalid.yml": DELVE},
        {"test-pkg/Large.yml": b" " * (1024 * 1024 + 1)},
    ]
)
def bad_archive(request, tmp_path, package_server):
    """GIVEN an invalid archive WHEN synced THEN reject its contents."""
    package_server.store("test-pkg", request.param)
    return Config(root=tmp_path, packages=[package_server.url("test-pkg")]), "test-pkg"


def test_invalid_archive(bad_archive):
    """GIVEN an invalid archive WHEN synced THEN name the package."""
    config, expected = bad_archive
    with pytest.raises(PackageError) as error:
        sync_packages(config)
    assert expected in str(error.value)


@pytest.fixture(
    params=[
        b"extends: script\nmessage: Bad.\n",
        b"extends: existence\nmessage: Bad.\ntokens: ['[']\n",
        b"extends: existence\nmessage: Bad.\ntokens: [delve]\nunknown: true\n",
        (b"extends: existence\nmessage: Bad.\ntokens: [delve]\ntokens: [other]\n"),
        (b"extends: existence\nmessage: Bad.\ntokens: [delve]\naction: {name: edit}\n"),
        b"extends: existence\nmessage: Bad.\ntokens: [delve]\nscope: table\n",
        b"extends: existence\nmessage: '%[2]s'\ntokens: [delve]\n",
        b"extends: substitution\nmessage: '%s'\nswap: {delve: '$1'}\n",
        b"extends: occurrence\nmessage: Bad.\ntoken: very\nmin: 3\nmax: 1\n",
        b"extends: occurrence\nmessage: Bad.\ntoken: very\nmax: true\n",
        b"extends: sequence\nmessage: Bad.\ntokens: [{tag: NN}]\n",
        (b"extends: sequence\nmessage: Bad.\ntokens: [{pattern: delve, skip: -1}]\n"),
        b"extends: existence\nmessage: Bad.\ntokens: ['a*']\n",
        b"- not a rule\n",
        b"\xff",
        DELVE + b"---\nextends: existence\nmessage: Bad.\ntokens: [other]\n",
    ]
)
def invalid_rule(request, tmp_path, package_server):
    """GIVEN a bad rule WHEN synced THEN reject it before publication."""
    package_server.store("test-pkg", {"test-pkg/Rule.yml": request.param})
    return Config(
        root=tmp_path, packages=[package_server.url("test-pkg")]
    ), "test-pkg.Rule"


def test_invalid_rule(invalid_rule):
    """GIVEN a bad rule WHEN synced THEN name the rule in the error."""
    config, expected = invalid_rule
    with pytest.raises(PackageError) as error:
        sync_packages(config)
    assert expected in str(error.value)


@pytest.fixture(params=["symlink", "duplicate", "not-zip"])
def invalid_zip(request, tmp_path, package_server):
    """GIVEN unsafe ZIP data WHEN synced THEN reject the archive."""
    output = io.BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("test-pkg/Delve.yml", DELVE)
        if request.param == "symlink":
            info = ZipInfo("link")
            info.external_attr = 0o120777 << 16
            archive.writestr(info, b"outside")
        elif request.param == "duplicate":
            with pytest.warns(UserWarning):
                archive.writestr("test-pkg/Delve.yml", DELVE)
    data = b"invalid" if request.param == "not-zip" else output.getvalue()
    (package_server.root / "test-pkg.zip").write_bytes(data)
    return Config(root=tmp_path, packages=[package_server.url("test-pkg")]), "test-pkg"


def test_invalid_zip(invalid_zip):
    """GIVEN invalid ZIP data WHEN synced THEN report the package."""
    config, expected = invalid_zip
    with pytest.raises(PackageError) as error:
        sync_packages(config)
    assert expected in str(error.value)


@pytest.fixture
def failed_sync(tmp_path, package_server):
    """GIVEN a valid cache WHEN the next download fails THEN keep it."""
    package_server.store("test-pkg", {"test-pkg/Delve.yml": DELVE})
    config = Config(root=tmp_path, packages=[package_server.url("test-pkg")])
    sync_packages(config)
    path = tmp_path / ".slop_away/packages/test-pkg.zip"
    expected = path.read_bytes()
    package_server.store("test-pkg", {"test-pkg/Delve.yml": b"invalid"})
    return config, path, expected


def test_failed_sync_preserves_cache(failed_sync):
    """GIVEN a valid cache WHEN sync fails THEN preserve its contents."""
    config, path, expected = failed_sync
    with pytest.raises(PackageError):
        sync_packages(config)
    assert path.read_bytes() == expected


@pytest.fixture
def multiple_packages(tmp_path, package_server):
    """GIVEN two packages WHEN one fails THEN preserve all old caches."""
    package_server.store("first", {"first/Delve.yml": DELVE})
    initial = Config(root=tmp_path, packages=[package_server.url("first")])
    sync_packages(initial)
    path = tmp_path / ".slop_away/packages/first.zip"
    expected = path.read_bytes()
    package_server.store("first", {"first/Delve.yml": DELVE + b"\n# New.\n"})
    config = Config(
        root=tmp_path,
        packages=[package_server.url("first"), package_server.url("missing")],
    )
    return config, path, expected


def test_sync_validates_all_downloads_before_publication(multiple_packages):
    """GIVEN a failed download WHEN syncing THEN keep all prior caches."""
    config, path, expected = multiple_packages
    with pytest.raises(PackageError):
        sync_packages(config)
    assert path.read_bytes() == expected


@pytest.fixture(params=["hash", "url", "version", "extra", "missing", "broken"])
def corrupt_cache(request, tmp_path, package_server):
    """GIVEN a changed cache WHEN checked THEN reject the cache."""
    package_server.store("test-pkg", {"test-pkg/Delve.yml": DELVE})
    config = Config(
        root=tmp_path,
        packages=[package_server.url("test-pkg")],
        select=["INJ"],
    )
    sync_packages(config)
    path = tmp_path / ".slop_away/packages/test-pkg.zip"
    with ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    manifest = json.loads(members["manifest.json"])
    if request.param in {"url", "version"}:
        manifest[request.param] = "changed"
    elif request.param == "hash":
        members["rules/Delve.yml"] += b"\n# Changed.\n"
    elif request.param == "extra":
        members["extra"] = b""
    members["manifest.json"] = json.dumps(manifest).encode()
    with ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    if request.param == "missing":
        path.unlink()
    elif request.param == "broken":
        path.write_bytes(b"invalid")
    return config, "test-pkg"


def test_invalid_cache_fails_even_when_excluded(corrupt_cache):
    """GIVEN an invalid excluded cache WHEN checked THEN fail fast."""
    config, expected = corrupt_cache
    with pytest.raises(PackageError) as error:
        check_text("The tool runs.", "a.md", config)
    assert expected in str(error.value)


@pytest.fixture(
    params=[
        ["http://example.com/pkg.zip"],
        ["file:///tmp/pkg.zip"],
        ["https://user:pass@example.com/pkg.zip"],
        ["https://example.com/pkg.zip#x"],
        ["https://example.com/no.zip?", "https://elsewhere.example/no.zip"],
        ["https://example.com/STE.zip"],
        ["https://example.com/1pkg.zip"],
        ["https://example.com/pkg.tar.gz"],
        ["https://example.com:0/pkg.zip"],
    ]
)
def invalid_urls(request):
    """GIVEN invalid package URLs WHEN configured THEN reject them."""
    return request.param, "packages"


def test_invalid_package_urls(invalid_urls):
    """GIVEN invalid URLs WHEN config is built THEN report packages."""
    urls, expected = invalid_urls
    with pytest.raises(ConfigError) as error:
        Config(packages=urls)
    assert expected in str(error.value)


@pytest.fixture(
    params=[
        {},
        {"select": ["test-pkg.Delve"]},
        {"select": ["INJ", "VRB", "RDB", "STE", "MSG"]},
        {"profiles": {"a.md": {"ignore": ["test-pkg"]}}},
    ]
)
def selection_case(request, tmp_path, package_server):
    """GIVEN package settings WHEN checked THEN apply exact selectors."""
    settings = request.param
    expected = (
        ["test-pkg.Delve"]
        if not settings or settings.get("select") == ["test-pkg.Delve"]
        else []
    )
    package_server.store("test-pkg", {"test-pkg/Delve.yml": DELVE})
    config = Config(
        root=tmp_path, packages=[package_server.url("test-pkg")], **settings
    )
    sync_packages(config)
    return config, expected


def test_package_selection(selection_case):
    """GIVEN selectors WHEN prose is checked THEN apply package selection."""
    config, expected = selection_case
    findings = check_text("We delve into the parser.", "a.md", config)
    actual = [item.code for item in findings if "." in item.code]
    assert actual == expected


@pytest.fixture
def unknown_selector(tmp_path, package_server):
    """GIVEN a missing rule selector WHEN checked THEN reject the name."""
    package_server.store("test-pkg", {"test-pkg/Delve.yml": DELVE})
    config = Config(
        root=tmp_path,
        packages=[package_server.url("test-pkg")],
        select=["test-pkg.Missing"],
    )
    sync_packages(config)
    return config, "test-pkg.Missing"


def test_unknown_rule_selector(unknown_selector):
    """GIVEN an unknown rule WHEN checked THEN name the invalid selector."""
    config, expected = unknown_selector
    with pytest.raises(PackageError) as error:
        check_files(paths=[], config=config)
    assert expected in str(error.value)


@pytest.fixture
def offline_package(cli, package_server):
    """GIVEN a synced package WHEN offline THEN use only its cache."""
    package_server.store("test-pkg", {"test-pkg/Delve.yml": DELVE})
    config = Config(root=cli.root, packages=[package_server.url("test-pkg")])
    sync_packages(config)
    (cli.root / "slop_away.toml").write_text(
        f'packages = ["{config.packages[0]}"]\nselect = ["test-pkg"]\n'
    )
    (cli.root / "a.md").write_text("We delve into the parser.")
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
    return CliHarness(cli.root, {"PYTHONPATH": str(directory)}), (1, True, "")


def test_offline_package_cli(offline_package):
    """GIVEN blocked sockets WHEN CLI checks a cache THEN report matches."""
    cli, expected = offline_package
    result = cli.run(["slop_away", "check", "a.md"])
    actual = (
        result.returncode,
        "test-pkg.Delve" in result.stdout,
        result.stderr,
    )
    assert actual == expected


@pytest.fixture(
    params=[
        (
            {},
            "We **delve** into the parser.",
            "a.md",
            [(1, 6, "Avoid delve.")],
        ),
        ({}, "The tool runs.\r\nWe delve.", "a.md", [(2, 4, "Avoid delve.")]),
        ({}, "We delve.", "AGENTS.md", []),
        (
            {},
            (
                "---\ntitle: delve\n---\n`delve`\n\n```\ndelve\n```\n"
                "\n<!-- delve -->\n\n| delve |\n| --- |\n| delve |\n"
            ),
            "a.md",
            [],
        ),
        (
            {"scope": "heading"},
            "# delve\n\nWe delve.",
            "a.md",
            [(1, 3, "Avoid delve.")],
        ),
        (
            {"scope": "h2"},
            "# delve\n\n## delve",
            "a.md",
            [(3, 4, "Avoid delve.")],
        ),
        (
            {"scope": ["~heading"]},
            "# delve\n\nWe delve.",
            "a.md",
            [(3, 4, "Avoid delve.")],
        ),
        (
            {"scope": "list"},
            "We delve.\n\n- delve",
            "a.md",
            [(3, 3, "Avoid delve.")],
        ),
        ({"ignorecase": True}, "We DELVE.", "a.md", [(1, 4, "Avoid DELVE.")]),
        ({"exceptions": ["delve"]}, "We delve.", "a.md", []),
        (
            {"limit": 1},
            "We delve and delve.",
            "a.md",
            [(1, 4, "Avoid delve.")],
        ),
        (
            {"scope": "raw", "tokens": [r"\*\*delve\*\*"], "nonword": True},
            "We **delve**.",
            "a.md",
            [(1, 4, "Avoid **delve**.")],
        ),
        (
            {"tokens": ["delve into"]},
            "We delve\ninto the parser.",
            "a.md",
            [(1, 4, "Avoid delve into.")],
        ),
        (
            {
                "extends": "substitution",
                "swap": {"(delv)e": "$1ing"},
                "message": "Use %s for %s.",
            },
            "We delve.",
            "a.md",
            [(1, 4, "Use delving for delve.")],
        ),
        (
            {
                "extends": "occurrence",
                "token": "very",
                "max": 1,
                "scope": "sentence",
                "message": "Count: %d.",
            },
            "Very fast. It is very very fast.",
            "a.md",
            [(1, 18, "Count: 2.")],
        ),
        (
            {
                "extends": "occurrence",
                "token": "very",
                "min": 1,
                "scope": "paragraph",
                "message": "Count: %d.",
            },
            "Fast.\n\nVery fast.",
            "a.md",
            [(1, 1, "Count: 0."), (3, 1, "Count: 0.")],
        ),
        (
            {
                "extends": "sequence",
                "tokens": [{"pattern": "seamless"}, {"tag": "NN"}],
                "message": "Avoid %s %s.",
            },
            "It gives a seamless experience.",
            "a.md",
            [(1, 12, "Avoid seamless experience.")],
        ),
        (
            {
                "extends": "sequence",
                "tokens": [
                    {"pattern": "seamless", "skip": 1},
                    {"tag": "NN", "target": True},
                ],
                "message": "Avoid %[2]s.",
            },
            "It gives a seamless new experience.",
            "a.md",
            [(1, 25, "Avoid experience.")],
        ),
        (
            {
                "extends": "sequence",
                "tokens": [
                    {"tag": "NN", "negate": True},
                    {"pattern": "Tools"},
                ],
                "message": "Avoid %[2]s.",
            },
            "Tools run.",
            "a.md",
            [(1, 1, "Avoid Tools.")],
        ),
        (
            {
                "extends": "sequence",
                "tokens": [{"pattern": "very", "min": 2}],
                "message": "Avoid %s.",
            },
            "It is very very fast.",
            "a.md",
            [(1, 7, "Avoid very very.")],
        ),
        (
            {
                "extends": "sequence",
                "tokens": [
                    {"pattern": "dog|cat", "min": 2, "skip": 8},
                    {"pattern": "it", "target": True},
                ],
                "message": "Avoid %[2]s.",
            },
            "The dog chased the cat until it tired.",
            "a.md",
            [(1, 30, "Avoid it.")],
        ),
        (
            {
                "extends": "sequence",
                "tokens": [{"pattern": "very", "min": 2}, {"pattern": "fast"}],
                "message": "Avoid %s %s.",
            },
            "It is very very very fast.",
            "a.md",
            [(1, 7, "Avoid very very very fast.")],
        ),
        (
            {
                "extends": "sequence",
                "tokens": [{"pattern": "seamless"}, {"tag": "NN"}],
                "exceptions": ["seamless experience"],
            },
            "It gives a seamless experience.",
            "a.md",
            [],
        ),
    ]
)
def rule_case(request, tmp_path, package_server):
    """GIVEN rule fields WHEN checked THEN apply their public behavior."""
    changes, text, path, expected = request.param
    kind = changes.get("extends", "existence")
    data = {"extends": kind, "message": "Avoid %s."}
    if kind == "existence":
        data["tokens"] = ["delve"]
    data.update(changes)
    package_server.store(
        "test-pkg", {"test-pkg/Rule.yml": yaml.safe_dump(data).encode()}
    )
    config = Config(
        root=tmp_path,
        packages=[package_server.url("test-pkg")],
        select=["test-pkg"],
    )
    sync_packages(config)
    return text, path, config, expected


def test_external_rule_behavior(rule_case):
    """GIVEN a cached rule WHEN checked THEN return its source findings."""
    text, path, config, expected = rule_case
    findings = check_text(text, path, config)
    actual = [(item.line, item.column, item.message) for item in findings]
    assert actual == expected
