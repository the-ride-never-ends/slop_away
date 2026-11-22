"""Supply shared test fixtures."""

from pathlib import Path

import pytest

from tests.harnesses import ApiHarness, CliHarness

pytest_plugins = ["tests.steps"]


@pytest.fixture(autouse=True)
def project_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """GIVEN a test project WHEN a test runs THEN use its directory."""
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def api() -> ApiHarness:
    """Supply the API test tool.

    Returns:
        The API test tool.
    """
    return ApiHarness()


@pytest.fixture
def cli(tmp_path: Path) -> CliHarness:
    """Supply a command test project.

    Args:
        tmp_path: The test directory.

    Returns:
        The command test tool.
    """
    (tmp_path / ".git").mkdir()
    return CliHarness(tmp_path)
