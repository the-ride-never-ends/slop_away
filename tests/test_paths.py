"""Test file selection at project boundaries."""

import pytest

from slop_away import Config, select_files


@pytest.fixture(
    params=[
        ("", "", ["."], {}, ["a.md", "docs/b.md", "docs/keep.md"]),
        ("*.md\n!a.md", "!keep.md", ["."], {}, ["a.md", "docs/keep.md"]),
        ("docs/\n!docs/keep.md", "", ["docs/keep.md"], {}, []),
        ("", "", ["a.md"], {"exclude": ["a.md"]}, []),
        ("", "", ["**/*.md"], {}, ["a.md", "docs/b.md", "docs/keep.md"]),
        ("", "", ["."], {"include": ["a.md"]}, ["a.md"]),
    ]
)
def path_case(tmp_path, request):
    """GIVEN project patterns WHEN selected THEN return matching paths."""
    root_ignore, nested_ignore, paths, settings, expected = request.param
    (tmp_path / "docs").mkdir()
    for name in ("a.md", "docs/b.md", "docs/keep.md", "note.txt"):
        (tmp_path / name).write_text("", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(root_ignore, encoding="utf-8")
    (tmp_path / "docs/.gitignore").write_text(nested_ignore, encoding="utf-8")
    return paths, Config(root=tmp_path, **settings), expected


def test_project_patterns(path_case):
    """GIVEN project patterns WHEN selected THEN return the expected paths."""
    paths, config, expected = path_case
    selected = select_files(paths, config)
    actual = [path.relative_to(config.root).as_posix() for path in selected]
    assert actual == expected


@pytest.fixture(params=[[], ["**/*.md"], ["link.md"], ["linked"]])
def symbolic_case(tmp_path, request):
    """GIVEN symbolic links WHEN selected THEN skip those links."""
    target = tmp_path / "real"
    target.mkdir()
    (target / "a.md").write_text("", encoding="utf-8")
    (tmp_path / "link.md").symlink_to(target / "a.md")
    (tmp_path / "linked").symlink_to(target, target_is_directory=True)
    paths = request.param
    expected = [target / "a.md"] if paths == ["**/*.md"] else []
    return paths, Config(root=tmp_path), expected


def test_symbolic_paths(symbolic_case):
    """GIVEN symbolic links WHEN selected THEN return only regular paths."""
    paths, config, expected = symbolic_case
    actual = select_files(paths, config)
    assert actual == expected


@pytest.fixture
def missing_case(tmp_path):
    """GIVEN an unmatched pattern WHEN selected THEN report that pattern."""
    pattern = "missing/**/*.md"
    return [pattern], Config(root=tmp_path), pattern


def test_missing_pattern(missing_case):
    """GIVEN an unmatched pattern WHEN selected THEN raise a named error."""
    paths, config, expected = missing_case
    with pytest.raises(FileNotFoundError) as caught:
        select_files(paths, config)
    assert expected in str(caught.value)


@pytest.fixture
def outside_case(tmp_path):
    """GIVEN an external path WHEN selected THEN reject that path."""
    outside = tmp_path.parent / "outside.md"
    return [outside], Config(root=tmp_path), str(outside)


def test_outside_path(outside_case):
    """GIVEN an external path WHEN selected THEN raise a named error."""
    paths, config, expected = outside_case
    with pytest.raises(ValueError) as caught:
        select_files(paths, config)
    assert expected in str(caught.value)
