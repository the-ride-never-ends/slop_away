"""Supply package test projects and feature steps."""

import ast
import io
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from zipfile import ZipFile

import pytest
from pytest_bdd import given, parsers, then

from slop_away import Config, Finding, sync_packages

DELVE = b"extends: existence\nmessage: Avoid '%s'.\ntokens: [delve]\n"


class PackageServer:
    """Serve test package archives."""

    def __init__(self, root: Path):
        """Start the package server.

        Args:
            root: The download directory.
        """
        self.root = root
        handler = partial(SimpleHTTPRequestHandler, directory=str(root))
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = Thread(
            target=self.server.serve_forever,
            kwargs={"poll_interval": 0.01},
            daemon=True,
        )
        self.thread.start()
        self.active = True

    def url(self, name: str) -> str:
        """Get a package URL.

        Args:
            name: The package name.

        Returns:
            The package URL.
        """
        return f"http://127.0.0.1:{self.server.server_port}/{name}.zip"

    def store(self, name: str, rules: dict[str, bytes]) -> None:
        """Store a test archive.

        Args:
            name: The package name.
            rules: Archive member names and contents.
        """
        output = io.BytesIO()
        with ZipFile(output, "w") as archive:
            for path, data in rules.items():
                archive.writestr(path, data)
        (self.root / f"{name}.zip").write_bytes(output.getvalue())

    def stop(self) -> None:
        """Stop the package server."""
        if self.active:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join()
            self.active = False


@pytest.fixture
def package_server(tmp_path):
    """GIVEN packages WHEN sync runs THEN serve local archives."""
    directory = tmp_path / "downloads"
    directory.mkdir()
    server = PackageServer(directory)
    yield server
    server.stop()


@given(parsers.parse('a local server that serves the package "{name}"'))
def serve_package(package_server, name):
    """GIVEN a package WHEN downloaded THEN supply its rule archive."""
    package_server.store(name, {f"{name}/Delve.yml": DELVE})


@given(
    parsers.parse(
        'a file "{path}" that lists the package "{name}" from the local server'
    )
)
def package_config(tmp_path, package_server, path, name):
    """GIVEN a server WHEN config loads THEN use its package URL."""
    (tmp_path / path).write_text(
        f'packages = ["{package_server.url(name)}"]\n', encoding="utf-8"
    )


@given('I have run "slop_away sync"')
def initial_sync(cli):
    """GIVEN a package WHEN checks run THEN prepare its cache."""
    cli.run(["slop_away", "sync"]).check_returncode()


@given("the local server is stopped")
def stop_server(package_server):
    """GIVEN a cache WHEN checks run THEN remove the download server."""
    package_server.stop()


@given(
    parsers.parse('a synced package "{name}" with the rule file "{filename}":')
)
def cached_rule(tmp_path, package_server, name, filename, docstring):
    """GIVEN a rule WHEN checks run THEN prepare its package cache."""
    package_server.store(name, {f"{name}/{filename}": docstring.encode()})
    sync_packages(Config(root=tmp_path, packages=[package_server.url(name)]))


@given(
    parsers.parse('a config that lists the package "{name}"'),
    target_fixture="config",
)
def listed_package(tmp_path, package_server, name):
    """GIVEN a package WHEN checked THEN enable its rules."""
    return Config(root=tmp_path, packages=[package_server.url(name)])


@given(
    parsers.parse(
        'a config that lists the package "{name}" with {key} {value}'
    ),
    target_fixture="config",
)
def selected_package(tmp_path, package_server, name, key, value):
    """GIVEN package selectors WHEN checked THEN use those settings."""
    return Config(
        root=tmp_path,
        packages=[package_server.url(name)],
        **{key: ast.literal_eval(value)},
    )


@then(parsers.parse('the package cache contains "{name}"'))
def cached_package(tmp_path, name):
    """GIVEN a sync WHEN complete THEN keep the package in its cache."""
    actual = (tmp_path / ".slop_away" / "packages" / f"{name}.zip").is_file()
    assert actual, f"Expected cached package {name}; got {actual}."


@then(parsers.parse("that finding has column {column:d}"))
def package_column(findings, column):
    """GIVEN a rule match WHEN reported THEN use its source column."""
    actual = [finding.column for finding in findings if "." in finding.code]
    expected = [column]
    assert actual == expected, f"Expected columns {expected}; got {actual}."


@then(parsers.parse('that finding\'s message contains "{text}"'))
def package_message(findings: list[Finding], text: str):
    """GIVEN a replacement WHEN reported THEN name the preferred text."""
    actual = [finding.message for finding in findings]
    assert any(text in message for message in actual), (
        f"Expected {text!r} in messages; got {actual}."
    )


@then(
    parsers.parse(
        'every finding from the package has a code starting with "{prefix}"'
    )
)
def package_codes(findings, prefix):
    """GIVEN package findings WHEN reported THEN use the package name."""
    actual = [finding.code for finding in findings if "." in finding.code]
    assert actual and all(code.startswith(prefix) for code in actual), (
        f"Expected codes with prefix {prefix}; got {actual}."
    )
