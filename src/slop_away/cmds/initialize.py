"""Prepare project configuration and agent hooks."""

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from slop_away.utils.write import write_text

SLOP_REPO = "https://github.com/the-ride-never-ends/slop_away"
SLOP_REV = "091ebf22b9f7e479a1fd10ad0d2497b306500998"
REPOSITORIES: list[dict[str, Any]] = [
    {
        "repo": SLOP_REPO,
        "rev": SLOP_REV,
        "hooks": [
            {"id": "slop_away-sync", "language_version": "python3.14"},
            {"id": "slop_away", "language_version": "python3.14"},
            {"id": "slop_away-msg", "language_version": "python3.14"},
        ],
    },
    {
        "repo": "https://github.com/lycheeverse/lychee",
        "rev": "lychee-v0.24.2",
        "hooks": [{"id": "lychee", "types": ["markdown"], "stages": ["pre-commit"]}],
    },
    {
        "repo": "https://github.com/rvben/rumdl-pre-commit",
        "rev": "v0.2.78",
        "hooks": [{"id": "rumdl", "stages": ["pre-commit"]}],
    },
]
EVENTS = {
    "PostToolUse": ("Write|Edit", "slop_away_post_edit.sh"),
    "Stop": (None, "slop_away_stop.sh"),
    "PreToolUse": ("Bash", "slop_away_pre_bash.sh"),
}


class ProjectLoader(yaml.SafeLoader):
    """Read project YAML with unique explicit keys."""

    def construct_mapping(self, node: Any, deep: bool = False) -> Any:
        """Read a project mapping.

        Args:
            node: The YAML mapping node.
            deep: Read child nodes in full.

        Returns:
            The project mapping.

        Raises:
            ValueError: An explicit key occurs twice.
        """
        keys = set()
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in keys:
                raise ValueError("Project keys must be unique strings.")
            keys.add(key)
        self.flatten_mapping(node)
        return super().construct_mapping(node, deep=deep)


def _read(path: Path) -> str:
    """Read exact project text.

    Args:
        path: The source file.

    Returns:
        The UTF-8 text without line-ending changes.
    """
    with path.open(encoding="utf-8", newline="") as stream:
        return stream.read()


def _template(name: str) -> str:
    """Read a shipped project template.

    Args:
        name: The template name.

    Returns:
        The template text.
    """
    source = files("slop_away").joinpath("templates", name).read_text(encoding="utf-8")
    return source.replace("@SLOP_REV@", SLOP_REV)


def _precommit(path: Path) -> str:
    """Add the project pre-commit hooks.

    Args:
        path: The target config file.

    Returns:
        The merged configuration.

    Raises:
        ValueError: The existing configuration is invalid.
    """
    data = (
        yaml.load(_read(path), Loader=ProjectLoader) if path.exists() else {"repos": []}
    )
    if not isinstance(data, dict) or not isinstance(data.get("repos"), list):
        raise TypeError(f"{path}: expected a repos list.")
    repos = data["repos"]
    for repo in repos:
        if (
            not isinstance(repo, dict)
            or not isinstance(repo.get("repo"), str)
            or not isinstance(repo.get("hooks"), list)
            or any(
                not isinstance(hook, dict) or not isinstance(hook.get("id"), str)
                for hook in repo["hooks"]
            )
        ):
            raise ValueError(f"{path}: invalid repository or hook entry.")
    stages = data.get("default_install_hook_types", ["pre-commit"])
    if not isinstance(stages, list) or any(
        not isinstance(stage, str) for stage in stages
    ):
        raise ValueError(f"{path}: expected hook type strings.")
    data["default_install_hook_types"] = list(
        dict.fromkeys(stages + ["pre-commit", "commit-msg"])
    )
    for addition in REPOSITORIES:
        existing = [
            repo
            for repo in repos
            if repo["repo"].rstrip("/").removesuffix(".git") == addition["repo"]
        ]
        if len(existing) > 1:
            raise ValueError(f"{path}: duplicate repository {addition['repo']}.")
        if existing:
            hooks = existing[0]["hooks"]
            ids = {hook["id"] for hook in hooks}
            hooks.extend(
                hook.copy() for hook in addition["hooks"] if hook["id"] not in ids
            )
        else:
            repos.append(
                {
                    **addition,
                    "hooks": [hook.copy() for hook in addition["hooks"]],
                }
            )
    return str(yaml.safe_dump(data, sort_keys=False))


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Read unique settings fields.

    Args:
        pairs: The settings names and values.

    Returns:
        The settings object.

    Raises:
        ValueError: A field occurs twice.
    """
    data = {}
    for name, value in pairs:
        if name in data:
            raise ValueError(f"Duplicate settings field {name!r}.")
        data[name] = value
    return data


def _settings(path: Path) -> str:
    """Add Claude Code event hooks.

    Args:
        path: The target settings file.

    Returns:
        The merged settings.

    Raises:
        ValueError: The existing hook settings are invalid.
    """
    data = json.loads(_read(path), object_pairs_hook=_object) if path.exists() else {}
    if not isinstance(data, dict) or not isinstance(data.get("hooks", {}), dict):
        raise TypeError(f"{path}: expected an object with hook settings.")
    hooks = data.setdefault("hooks", {})
    for entries in hooks.values():
        if not isinstance(entries, list) or any(
            not isinstance(entry, dict)
            or not isinstance(entry.get("hooks"), list)
            or any(not isinstance(hook, dict) for hook in entry["hooks"])
            for entry in entries
        ):
            raise ValueError(f"{path}: invalid hook entries.")
    for event, (matcher, script) in EVENTS.items():
        command = f'bash "$CLAUDE_PROJECT_DIR/.claude/hooks/{script}"'
        entries = hooks.setdefault(event, [])
        if any(
            entry.get("matcher") == matcher
            and any(hook.get("command") == command for hook in entry["hooks"])
            for entry in entries
        ):
            continue
        entry: dict[str, Any] = {"hooks": [{"type": "command", "command": command}]}
        if matcher is not None:
            entry["matcher"] = matcher
        entries.append(entry)
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _ignore(path: Path) -> str:
    """Add the cache directory to Git ignores.

    Args:
        path: The Git ignore file.

    Returns:
        The updated file text.
    """
    source = _read(path) if path.exists() else ""
    if any(
        line.strip() in {".slop_away/", "/.slop_away/"} for line in source.splitlines()
    ):
        return source
    ending = "\r\n" if "\r\n" in source else "\n"
    return (
        source
        + (ending if source and not source.endswith(("\n", "\r")) else "")
        + ".slop_away/"
        + ending
    )


def init_project(
    *,
    root: str | Path,
    skip_config: bool = False,
    skip_pre_commit: bool = False,
    skip_ci: bool = False,
    skip_hooks: bool = False,
) -> None:
    """Prepare project checks and agent hooks.

    Args:
        root: The target project directory.
        skip_config: Keep the project config out of the plan.
        skip_pre_commit: Keep pre-commit config out of the plan.
        skip_ci: Keep the CI workflow out of the plan.
        skip_hooks: Keep Claude Code scripts and settings out of the plan.

    Raises:
        ValueError: A target exists or existing settings are invalid.
        TypeError: A skip option is not a boolean.
        OSError: A project file cannot be read or written.
    """
    directory = Path(root).resolve()
    if not directory.is_dir():
        raise ValueError(f"{directory}: expected a project directory.")
    fresh = {}
    merge = {".gitignore": _ignore}
    if not skip_config:
        fresh["slop_away.toml"] = "slop_away.toml"
    if not skip_pre_commit:
        merge[".pre-commit-config.yaml"] = _precommit
    if not skip_ci:
        fresh[".github/workflows/slop_away.yml"] = "slop_away.yml"
    if not skip_hooks:
        merge[".claude/settings.json"] = _settings
        for _, script in EVENTS.values():
            fresh[f".claude/hooks/{script}"] = script
    for name in [*fresh, *merge]:
        target = directory / name
        for path in (target, *target.parents):
            if path == directory:
                break
            if (
                path.is_symlink()
                or path.exists()
                and path != target
                and not path.is_dir()
            ):
                raise ValueError(f"{path}: expected a project path without symlinks.")
        if name in fresh and target.exists():
            raise ValueError(f"{target}: target already exists.")
        if name in merge and target.exists() and not target.is_file():
            raise ValueError(f"{target}: expected a file.")
    pending = [
        (directory / name, _template(template)) for name, template in fresh.items()
    ]
    for name, merger in merge.items():
        path = directory / name
        try:
            pending.append((path, merger(path)))
        except (ValueError, TypeError, yaml.YAMLError) as error:
            raise ValueError(f"{path}: {error}") from error
    for path, text in pending:
        existed = path.exists()
        path.parent.mkdir(parents=True, exist_ok=True)
        mode = None if existed else 0o755 if path.suffix == ".sh" else 0o644
        write_text(
            path=path,
            text=text,
            mode=mode,
        )
