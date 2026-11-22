"""Supply API and command test tools."""

import os
import subprocess
import sysconfig
import textwrap
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path


class ApiHarness:
    """Call a public API in the test process."""

    def call[**P, T](
        self, function: Callable[P, T], *args: P.args, **kwargs: P.kwargs
    ) -> T:
        """Call a public function.

        Args:
            function: The public function to call.
            *args: Positional arguments for the function.
            **kwargs: Named arguments for the function.

        Returns:
            The function result.
        """
        return function(*args, **kwargs)


@dataclass(frozen=True)
class CliHarness:
    """Run commands in a test project."""

    root: Path
    environment: dict[str, str] = field(default_factory=dict)

    def run(
        self, arguments: Sequence[str]
    ) -> subprocess.CompletedProcess[str]:
        """Run one command.

        Args:
            arguments: The command and its arguments.

        Returns:
            The exit code and output.

        Raises:
            ValueError: The command is empty.
            TimeoutExpired: The command exceeds the time limit.
        """
        if not arguments:
            raise ValueError("The command must not be empty.")
        environment = os.environ.copy()
        environment["PATH"] = os.pathsep.join(
            (sysconfig.get_path("scripts"), os.defpath)
        )
        environment.update(self.environment)
        return subprocess.run(
            arguments,
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )


class GitHarness(CliHarness):
    """Check commits in a test repository."""

    def install(self, manifest: Path) -> None:
        """Install the test repository and its hook.

        Args:
            manifest: The hook manifest.
        """
        hook = manifest.read_text(encoding="utf-8").replace(
            "language: python", "language: system"
        )
        config = "repos:\n  - repo: local\n    hooks:\n" + textwrap.indent(
            hook, "      "
        )
        target = self.root / ".pre-commit-config.yaml"
        target.write_text(config, encoding="utf-8")
        for arguments in (
            ["git", "init", "--initial-branch=main"],
            ["git", "config", "user.name", "Test Author"],
            ["git", "config", "user.email", "test@example.com"],
            ["git", "add", ".pre-commit-config.yaml"],
            ["pre-commit", "install"],
        ):
            self.run(arguments).check_returncode()

    def stage(self, path: str, text: str) -> None:
        """Stage a document for a commit.

        Args:
            path: The document path.
            text: The document text.
        """
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        self.run(["git", "add", path]).check_returncode()
