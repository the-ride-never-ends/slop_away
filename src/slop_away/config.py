"""Read and check project settings."""

import re
import tomllib
from dataclasses import dataclass, field, replace
from math import isfinite
from pathlib import Path, PurePosixPath
from typing import Any, cast

from slop_away.package_types import parse_package

GROUP_LIMITS = {"INJ": 4, "VRB": 5, "RDB": 1, "STE": 7, "MSG": 4}
NATIVE_CODES = tuple(
    f"{group}{number:03}"
    for group, limit in GROUP_LIMITS.items()
    for number in range(1, limit + 1)
)


class ConfigError(ValueError):
    """Report invalid project settings."""


def _strings(value: object, key: str) -> None:
    """Require a list of nonempty strings.

    Args:
        value: The setting value.
        key: The setting name.

    Raises:
        ConfigError: The setting is invalid.
    """
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ConfigError(f"{key}: expected a list of nonempty strings.")


def _selectors(value: Any, key: str, packages: set[str]) -> None:
    """Check rule selectors.

    Args:
        value: The selector list.
        key: The setting name.
        packages: The configured package names.

    Raises:
        ConfigError: A selector is invalid.
    """
    _strings(value, key)
    for entry in value:
        native = any(code.startswith(entry) for code in NATIVE_CODES)
        external = entry in packages or any(
            entry.startswith(name + ".")
            and re.fullmatch(
                r"[A-Za-z][A-Za-z0-9_.-]*", entry[len(name) + 1 :]
            )
            for name in packages
        )
        if not native and not external:
            raise ConfigError(f"{key}: unknown rule selector {entry!r}.")


def _pattern(value: str, key: str) -> None:
    """Check a project path pattern.

    Args:
        value: The pattern.
        key: The setting name.

    Raises:
        ConfigError: The pattern is invalid.
    """
    path = PurePosixPath(value)
    if (
        not value.strip()
        or path.is_absolute()
        or ".." in path.parts
        or not value.rstrip("/")
    ):
        raise ConfigError(f"{key}: expected a project pattern.")


def _grade(value: object, key: str) -> None:
    """Check a grade limit.

    Args:
        value: The grade limit.
        key: The setting name.

    Raises:
        ConfigError: The limit is invalid.
    """
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or value < 0
        or isinstance(value, float)
        and not isfinite(value)
    ):
        raise ConfigError(f"{key}: expected a finite nonnegative number.")


def _budget(value: object, key: str) -> None:
    """Check a word budget.

    Args:
        value: The word budget, or None for no limit.
        key: The setting name.

    Raises:
        ConfigError: The budget is invalid.
    """
    if value is not None and (
        isinstance(value, bool) or not isinstance(value, int) or value < 0
    ):
        raise ConfigError(f"{key}: expected a nonnegative integer.")


def _profiles(value: Any, packages: set[str]) -> None:
    """Check file profiles.

    Args:
        value: The profile table.
        packages: The configured package names.

    Raises:
        ConfigError: A profile is invalid.
    """
    if not isinstance(value, dict):
        raise ConfigError("profiles: expected a table.")
    allowed = {"select", "ignore", "max-grade", "word-budget"}
    for pattern, settings in value.items():
        if not isinstance(pattern, str):
            raise ConfigError("profiles: expected string patterns.")
        _pattern(pattern, "profiles")
        key = f"profiles.{pattern}"
        if not isinstance(settings, dict):
            raise ConfigError(f"{key}: expected a settings table.")
        unknown = settings.keys() - allowed
        if unknown:
            raise ConfigError(f"{key}: unknown setting {min(unknown)}.")
        for selector in ("select", "ignore"):
            if selector in settings:
                _selectors(settings[selector], f"{key}.{selector}", packages)
        if "max-grade" in settings:
            _grade(settings["max-grade"], f"{key}.max-grade")
        if "word-budget" in settings:
            _budget(settings["word-budget"], f"{key}.word-budget")


def _glossary(value: Any) -> None:
    """Check the project terminology.

    Args:
        value: Preferred terms and their banned synonyms.

    Raises:
        ConfigError: A term or synonym is invalid or has two meanings.
    """
    if not isinstance(value, dict):
        raise ConfigError("glossary: expected a table.")
    preferred: set[str] = set()
    for term, synonyms in value.items():
        if (
            not isinstance(term, str)
            or not term.strip()
            or term != term.strip()
            or "\n" in term
            or "\r" in term
        ):
            raise ConfigError("glossary: expected nonempty single-line terms.")
        normalized = " ".join(term.casefold().split())
        if normalized in preferred:
            raise ConfigError(f"glossary: repeated preferred term {term!r}.")
        preferred.add(normalized)
        _strings(synonyms, f"glossary.{term}")
    banned: set[str] = set()
    for synonyms in value.values():
        for synonym in synonyms:
            if (
                synonym != synonym.strip()
                or "\n" in synonym
                or "\r" in synonym
            ):
                raise ConfigError("glossary: expected single-line synonyms.")
            normalized = " ".join(synonym.casefold().split())
            if normalized in preferred or normalized in banned:
                raise ConfigError(
                    f"glossary: conflicting synonym {synonym!r}."
                )
            banned.add(normalized)


def _ignores(value: Any, packages: set[str]) -> None:
    """Check per-file rule ignores.

    Args:
        value: The pattern and selector table.
        packages: The configured package names.

    Raises:
        ConfigError: A path pattern or selector is invalid.
    """
    if not isinstance(value, dict):
        raise ConfigError("per-file-ignores: expected a table.")
    for pattern, selectors in value.items():
        if not isinstance(pattern, str):
            raise ConfigError("per-file-ignores: expected string patterns.")
        _pattern(pattern, "per-file-ignores")
        _selectors(selectors, f"per-file-ignores.{pattern}", packages)


@dataclass
class Config:
    """Hold the project settings."""

    include: list[str] = field(default_factory=lambda: ["**/*.md"])
    exclude: list[str] = field(
        default_factory=lambda: [
            ".git",
            ".venv",
            "node_modules",
            "build",
            "dist",
        ]
    )
    extend_exclude: list[str] = field(default_factory=list)
    select: list[str] | None = None
    ignore: list[str] = field(default_factory=list)
    instruction_files: list[str] = field(
        default_factory=lambda: ["AGENTS.md", "CLAUDE.md", "SKILL.md"]
    )
    max_grade: int | float = 10
    word_budget: int | None = None
    profiles: dict[str, dict[str, Any]] = field(default_factory=dict)
    per_file_ignores: dict[str, list[str]] = field(default_factory=dict)
    glossary: dict[str, list[str]] = field(default_factory=dict)
    packages: list[str] = field(default_factory=list)
    root: Path = field(default_factory=Path.cwd, compare=False, repr=False)

    def __post_init__(self) -> None:
        """Check the settings.

        Raises:
            ConfigError: A setting is invalid.
        """
        self.root = Path(self.root).resolve()
        _strings(self.packages, "packages")
        names: set[str] = set()
        for url in self.packages:
            try:
                package = parse_package(url)
            except ValueError as error:
                raise ConfigError(f"packages: {error}") from error
            if package.name in names or any(
                code.startswith(package.name) for code in NATIVE_CODES
            ):
                raise ConfigError(
                    f"packages: duplicate or reserved name {package.name!r}."
                )
            names.add(package.name)
        if self.select is None:
            self.select = list(GROUP_LIMITS) + sorted(names)
        for key in (
            "include",
            "exclude",
            "extend_exclude",
            "instruction_files",
        ):
            _strings(getattr(self, key), key.replace("_", "-"))
        for key in ("select", "ignore"):
            _selectors(getattr(self, key), key, names)
        for key in ("include", "exclude", "extend_exclude"):
            for pattern in getattr(self, key):
                _pattern(pattern, key.replace("_", "-"))
        if any(Path(name).name != name for name in self.instruction_files):
            raise ConfigError("instruction-files: expected file names.")
        _grade(self.max_grade, "max-grade")
        _budget(self.word_budget, "word-budget")
        _profiles(self.profiles, names)
        _ignores(self.per_file_ignores, names)
        _glossary(self.glossary)

    def for_path(self, path: str | Path) -> Config:
        """Get settings for a document path.

        Args:
            path: The document path.

        Returns:
            Settings with matching profiles and per-file ignores applied.

        Raises:
            ValueError: An absolute path is outside the project.
        """
        relative = Path(path)
        if relative.is_absolute():
            relative = relative.relative_to(self.root)
        settings: dict[str, Any] = {}
        for pattern, profile in self.profiles.items():
            if PurePosixPath(relative.as_posix()).full_match(pattern):
                settings.update(
                    {
                        key.replace("-", "_"): value
                        for key, value in profile.items()
                    }
                )
        ignored = list(settings.get("ignore", self.ignore))
        for pattern, selectors in self.per_file_ignores.items():
            if PurePosixPath(relative.as_posix()).full_match(pattern):
                ignored.extend(selectors)
        if ignored != settings.get("ignore", self.ignore):
            settings["ignore"] = list(dict.fromkeys(ignored))
        return (
            replace(self, profiles={}, per_file_ignores={}, **settings)
            if settings
            else self
        )

    def enabled(self, code: str) -> bool:
        """Check whether a rule is selected.

        Args:
            code: The rule code.

        Returns:
            True if the rule is selected and is not ignored.
        """

        def matches(entry: str) -> bool:
            """Check a rule selector.

            Args:
                entry: The selector.

            Returns:
                True if the selector includes the rule.
            """
            if "." in code:
                return entry in {code, code.split(".", 1)[0]}
            return code.startswith(entry)

        return any(
            matches(entry) for entry in cast(list[str], self.select)
        ) and not any(matches(entry) for entry in self.ignore)


def _read_table(path: Path) -> dict[str, Any]:
    """Read a settings file.

    Args:
        path: The settings file.

    Returns:
        The settings table.

    Raises:
        ConfigError: The file cannot be read or contains invalid TOML.
    """
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ConfigError(f"{path}: {error}") from error


def _project_table(path: Path) -> dict[str, Any] | None:
    """Read the tool settings from a project file.

    Args:
        path: The project file.

    Returns:
        The tool settings, or None if the section is absent.

    Raises:
        ConfigError: A settings section is not a table.
    """
    tool = _read_table(path).get("tool", {})
    if not isinstance(tool, dict):
        raise ConfigError(f"{path}: tool must be a table.")
    settings = tool.get("slop_away")
    if settings is not None and not isinstance(settings, dict):
        raise ConfigError(f"{path}: tool.slop_away must be a table.")
    return settings


def load_config(root: str | Path) -> Config:
    """Read the project settings.

    Args:
        root: The project directory.

    Returns:
        The project settings, or the default settings if no file applies.

    Raises:
        ConfigError: The directory or settings are invalid.
    """
    directory = Path(root).resolve()
    if not directory.is_dir():
        raise ConfigError(f"{directory}: expected a project directory.")
    standalone = directory / "slop_away.toml"
    project = directory / "pyproject.toml"
    settings: dict[str, Any] = {}
    if standalone.exists():
        settings = _read_table(standalone)
    elif project.exists():
        table = _project_table(project)
        if table is not None:
            settings = table
    allowed = {
        "include",
        "exclude",
        "extend-exclude",
        "select",
        "ignore",
        "instruction-files",
        "max-grade",
        "word-budget",
        "profiles",
        "per-file-ignores",
        "glossary",
        "packages",
    }
    unknown = settings.keys() - allowed
    if unknown:
        raise ConfigError(f"Unknown config key: {min(unknown)}.")
    return Config(
        root=directory,
        **{key.replace("-", "_"): value for key, value in settings.items()},
    )


def find_root(start: Path) -> Path:
    """Find the project directory for a command.

    Args:
        start: The command directory.

    Returns:
        The nearest config or Git directory, or the command directory.
    """
    directory = start.resolve()
    for candidate in (directory, *directory.parents):
        if (candidate / "slop_away.toml").exists():
            return candidate
        project = candidate / "pyproject.toml"
        if project.exists() and _project_table(project) is not None:
            return candidate
        if (candidate / ".git").exists():
            return candidate
    return directory
