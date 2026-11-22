"""Read and check project settings."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

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
    select: list[str] = field(default_factory=lambda: list(GROUP_LIMITS))
    ignore: list[str] = field(default_factory=list)
    instruction_files: list[str] = field(
        default_factory=lambda: ["AGENTS.md", "CLAUDE.md", "SKILL.md"]
    )
    root: Path = field(default_factory=Path.cwd, compare=False, repr=False)

    def __post_init__(self) -> None:
        """Check the settings.

        Raises:
            ConfigError: A setting is invalid.
        """
        self.root = Path(self.root).resolve()
        for key in (
            "include",
            "exclude",
            "extend_exclude",
            "select",
            "ignore",
            "instruction_files",
        ):
            _strings(getattr(self, key), key.replace("_", "-"))
        for key in ("select", "ignore"):
            for entry in getattr(self, key):
                if not any(code.startswith(entry) for code in NATIVE_CODES):
                    raise ConfigError(
                        f"{key}: unknown rule selector {entry!r}."
                    )
        for key in ("include", "exclude", "extend_exclude"):
            for pattern in getattr(self, key):
                path = PurePosixPath(pattern)
                if (
                    path.is_absolute()
                    or ".." in path.parts
                    or not pattern.rstrip("/")
                ):
                    raise ConfigError(
                        f"{key.replace('_', '-')}: expected a project pattern."
                    )
        if any(Path(name).name != name for name in self.instruction_files):
            raise ConfigError("instruction-files: expected file names.")

    def enabled(self, code: str) -> bool:
        """Check whether a rule is selected.

        Args:
            code: The rule code.

        Returns:
            True if the rule is selected and is not ignored.
        """
        return any(code.startswith(item) for item in self.select) and not any(
            code.startswith(item) for item in self.ignore
        )


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
