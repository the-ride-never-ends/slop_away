"""Supply API and command test tools."""

import os
import subprocess
import sysconfig
from collections.abc import Callable, Sequence
from dataclasses import dataclass
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
