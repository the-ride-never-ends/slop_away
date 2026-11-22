"""Select project Markdown files."""

from collections.abc import Iterator, Sequence
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath

from pathspec import GitIgnoreSpec

from slop_away.config import Config


def _matches(path: Path, pattern: str) -> bool:
    """Check a path pattern.

    Args:
        path: A relative path.
        pattern: The path pattern.

    Returns:
        True if the path or a parent matches.
    """
    pattern = pattern.rstrip("/")
    if "/" not in pattern:
        return any(fnmatchcase(part, pattern) for part in path.parts)
    return any(
        PurePosixPath(candidate.as_posix()).full_match(pattern)
        for candidate in (path, *path.parents)
    )


class _Selection:
    """Hold file selection settings for one run."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.ignores: dict[Path, GitIgnoreSpec] = {}

    def excluded(self, path: Path) -> bool:
        """Check whether a path is excluded.

        Args:
            path: The absolute path.

        Returns:
            True if config or Git patterns exclude the path.
        """
        relative = path.relative_to(self.config.root)
        patterns = self.config.exclude + self.config.extend_exclude
        if any(_matches(relative, pattern) for pattern in patterns):
            return True
        ignored = False
        directories = [self.config.root]
        directories.extend(
            self.config.root / parent
            for parent in reversed(relative.parents)
            if parent != Path(".")
        )
        for directory in directories:
            if directory not in self.ignores:
                ignore = directory / ".gitignore"
                lines = (
                    ignore.read_text(encoding="utf-8").splitlines()
                    if ignore.is_file()
                    else []
                )
                self.ignores[directory] = GitIgnoreSpec.from_lines(lines)
            local = path.relative_to(directory).as_posix()
            if path.is_dir():
                local += "/"
            result = self.ignores[directory].check_file(local)
            if result.include is not None:
                ignored = result.include
        return ignored

    def files(self, path: Path) -> Iterator[Path]:
        """List selected files below a path.

        Args:
            path: The input path.

        Yields:
            Absolute paths of selected Markdown files.
        """
        parents = (
            self.config.root / parent
            for parent in path.relative_to(self.config.root).parents
            if parent != Path(".")
        )
        if (
            path.is_symlink()
            or self.excluded(path)
            or any(self.excluded(parent) for parent in parents)
        ):
            return
        if path.is_dir():
            for child in sorted(path.iterdir()):
                yield from self.files(child)
        elif path.is_file() and path.suffix == ".md":
            relative = path.relative_to(self.config.root)
            if any(_matches(relative, item) for item in self.config.include):
                yield path


def select_files(paths: Sequence[str | Path], config: Config) -> list[Path]:
    """Select Markdown files from project paths.

    Args:
        paths: Paths or recursive glob patterns relative to the project.
        config: The project settings.

    Returns:
        Sorted, unique absolute paths.

    Raises:
        FileNotFoundError: An input path or glob has no match.
        ValueError: An input is outside the project directory.
        OSError: A directory or ignore file cannot be read.
    """
    selection = _Selection(config)
    selected: set[Path] = set()
    for item in paths:
        candidate = Path(item)
        if not candidate.is_absolute():
            candidate = config.root / candidate
        if candidate.is_symlink():
            continue
        candidate = candidate.resolve()
        if not candidate.is_relative_to(config.root):
            raise ValueError(f"Input is outside the project: {item}")
        matches = (
            [candidate]
            if candidate.exists()
            else list(
                config.root.glob(candidate.relative_to(config.root).as_posix())
            )
        )
        if not matches:
            raise FileNotFoundError(f"Input path has no match: {item}")
        for path in matches:
            if path.is_symlink():
                continue
            path = path.resolve()
            selected.update(selection.files(path))
    return sorted(selected)
