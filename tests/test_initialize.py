"""Test project initialization and merge contracts."""

import json

import pytest
import yaml  # type: ignore[import-untyped]

from slop_away import init_project


def snapshot(root):
    """GIVEN a project WHEN compared THEN record its paths and contents."""
    return {
        path.relative_to(root).as_posix(): ("link", str(path.readlink()))
        if path.is_symlink()
        else path.read_bytes()
        if path.is_file()
        else None
        for path in root.rglob("*")
    }


@pytest.fixture(
    params=[
        "slop_away.toml",
        ".github/workflows/slop_away.yml",
        ".claude/hooks/slop_away_post_edit.sh",
        ".claude/hooks/slop_away_stop.sh",
        ".claude/hooks/slop_away_pre_bash.sh",
    ]
)
def conflicting_target(request, tmp_path):
    """GIVEN an existing fresh target WHEN init runs THEN write nothing."""
    path = tmp_path / request.param
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Existing content.")
    return tmp_path, snapshot(tmp_path)


def test_init_conflicts_preserve_project(conflicting_target):
    """GIVEN a target conflict WHEN initialized THEN keep the whole tree."""
    root, expected = conflicting_target
    with pytest.raises(ValueError):
        init_project(root)
    assert snapshot(root) == expected


@pytest.fixture(
    params=[
        (".pre-commit-config.yaml", "repos: invalid\n"),
        (".pre-commit-config.yaml", "repos: []\nrepos: []\n"),
        (".pre-commit-config.yaml", "repos: [wrong]\n"),
        (".pre-commit-config.yaml", "repos: [{repo: local, hooks: wrong}]\n"),
        (
            ".pre-commit-config.yaml",
            "repos: []\ndefault_install_hook_types: wrong\n",
        ),
        (".claude/settings.json", "[]"),
        (".claude/settings.json", "invalid"),
        (".claude/settings.json", '{"hooks": null}'),
        (".claude/settings.json", '{"hooks": {"Stop": {}}}'),
        (".claude/settings.json", '{"hooks": {"Stop": [{"hooks": null}]}}'),
        (".claude/settings.json", '{"hooks": {}, "hooks": {}}'),
    ]
)
def invalid_merge(request, tmp_path):
    """GIVEN invalid merge data WHEN init runs THEN preserve all files."""
    name, source = request.param
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source)
    return tmp_path, snapshot(tmp_path)


def test_init_rejects_invalid_merge_data(invalid_merge):
    """GIVEN bad existing settings WHEN initialized THEN write no targets."""
    root, expected = invalid_merge
    with pytest.raises(ValueError):
        init_project(root)
    assert snapshot(root) == expected


@pytest.fixture(params=["parent-file", "link", "broken-link"])
def unsafe_target(request, tmp_path):
    """GIVEN an invalid target path WHEN init runs THEN preserve it."""
    if request.param == "parent-file":
        (tmp_path / ".claude").write_text("Not a directory.")
    else:
        target = tmp_path / "settings"
        if request.param == "link":
            target.write_text("{}")
        directory = tmp_path / ".claude"
        directory.mkdir()
        (directory / "settings.json").symlink_to(target)
    return tmp_path, snapshot(tmp_path)


def test_init_rejects_unsafe_target_paths(unsafe_target):
    """GIVEN unsafe target paths WHEN initialized THEN write no files."""
    root, expected = unsafe_target
    with pytest.raises(ValueError):
        init_project(root)
    assert snapshot(root) == expected


@pytest.fixture
def merged_settings(tmp_path):
    """GIVEN existing settings WHEN initialized THEN retain their values."""
    data = {
        "permissions": {"allow": ["Bash(ls)"]},
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "Write",
                    "hooks": [{"type": "command", "command": "echo existing"}],
                }
            ]
        },
    }
    directory = tmp_path / ".claude"
    directory.mkdir()
    path = directory / "settings.json"
    path.write_text(json.dumps(data))
    path.chmod(0o640)
    return (
        tmp_path,
        path,
        data["hooks"]["PostToolUse"][0],
        (["Bash(ls)"], 0o640, True),
    )


def test_init_preserves_existing_claude_hooks(merged_settings):
    """GIVEN existing hooks WHEN initialized THEN keep hooks and access."""
    root, path, hook, expected = merged_settings
    init_project(root)
    data = json.loads(path.read_text())
    retained = hook in data["hooks"]["PostToolUse"]
    mode = path.stat().st_mode & 0o777
    actual = data["permissions"]["allow"], mode, retained
    assert actual == expected


@pytest.fixture
def anchored_config(tmp_path):
    """GIVEN YAML aliases WHEN initialized THEN keep their config values."""
    path = tmp_path / ".pre-commit-config.yaml"
    path.write_text(
        "defaults: &defaults\n  language: system\nrepos:\n"
        "  - repo: local\n    hooks:\n      - <<: *defaults\n"
        "        id: custom\n        name: Custom\n"
        "        entry: echo custom\n"
    )
    return (
        tmp_path,
        path,
        {
            "language": "system",
            "id": "custom",
            "name": "Custom",
            "entry": "echo custom",
        },
    )


def test_init_preserves_yaml_merge_values(anchored_config):
    """GIVEN YAML merge values WHEN initialized THEN preserve the hook."""
    root, path, expected = anchored_config
    init_project(root)
    actual = yaml.safe_load(path.read_text())["repos"][0]["hooks"][0]
    assert actual == expected


@pytest.fixture
def existing_hooks(tmp_path):
    """GIVEN a prior setup WHEN adding checks THEN avoid duplicate IDs."""
    init_project(tmp_path)
    path = tmp_path / ".pre-commit-config.yaml"
    expected = yaml.safe_load(path.read_text())
    return tmp_path, path, expected


def test_init_merges_without_duplicate_hooks(existing_hooks):
    """GIVEN existing entries WHEN merged again THEN keep the same config."""
    root, path, expected = existing_hooks
    init_project(root, skip_config=True, skip_ci=True, skip_hooks=True)
    actual = yaml.safe_load(path.read_text())
    assert actual == expected


@pytest.fixture
def ignored_cache(tmp_path):
    """GIVEN Git ignore data WHEN initialized THEN preserve line endings."""
    path = tmp_path / ".gitignore"
    path.write_bytes(b"# Existing.\r\ndist/\r\n")
    return tmp_path, path, b"# Existing.\r\ndist/\r\n.slop_away/\r\n"


def test_init_preserves_gitignore_text(ignored_cache):
    """GIVEN existing ignores WHEN initialized THEN append the cache path."""
    root, path, expected = ignored_cache
    init_project(root)
    assert path.read_bytes() == expected


@pytest.fixture
def generated_hooks(cli):
    """GIVEN a new config WHEN validated THEN include both Git stages."""
    return cli, 0


def test_generated_precommit_config_is_valid(generated_hooks):
    """GIVEN generated hooks WHEN validated THEN pass the config check."""
    cli, expected = generated_hooks
    init_project(cli.root)
    result = cli.run(["pre-commit", "validate-config"])
    assert result.returncode == expected


@pytest.fixture(
    params=[
        "slop_away_post_edit.sh",
        "slop_away_stop.sh",
        "slop_away_pre_bash.sh",
    ]
)
def script_mode(request, tmp_path):
    """GIVEN generated scripts WHEN initialized THEN make them executable."""
    return tmp_path, request.param, 0o755


def test_init_sets_script_permissions(script_mode):
    """GIVEN a new hook script WHEN initialized THEN permit execution."""
    root, name, expected = script_mode
    init_project(root)
    actual = (root / ".claude/hooks" / name).stat().st_mode & 0o777
    assert actual == expected


@pytest.fixture
def hook_ids(tmp_path):
    """GIVEN a new project WHEN initialized THEN include all check hooks."""
    expected = (
        ["pre-commit", "commit-msg"],
        ["slop_away-sync", "slop_away", "slop_away-msg", "lychee", "rumdl"],
    )
    return tmp_path, expected


def test_init_includes_required_integrations(hook_ids):
    """GIVEN project setup WHEN initialized THEN include all integrations."""
    root, expected = hook_ids
    init_project(root)
    data = yaml.safe_load((root / ".pre-commit-config.yaml").read_text())
    ids = [hook["id"] for repo in data["repos"] for hook in repo["hooks"]]
    actual = data["default_install_hook_types"], ids
    assert actual == expected
