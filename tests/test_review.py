"""Test the review check for protected files."""

import json
import subprocess
from pathlib import Path

import pytest
import yaml


@pytest.fixture(
    params=[
        ([{"filename": "src/slop_away/config.py"}], [], None, []),
        ([{"filename": "slop_away.toml"}], [], None, ["label"]),
        ([{"filename": "pyproject.toml"}], [], None, ["label"]),
        ([{"filename": "slop_away.baseline.json"}], [], None, ["label"]),
        ([{"filename": ".github/workflows/new.yml"}], [], None, ["label"]),
        ([{"filename": "CODEOWNERS"}], [], None, ["label"]),
        ([{"filename": "docs/CODEOWNERS"}], [], None, ["label"]),
        ([{"filename": "slop_away.toml"}], ["owner-approved"], None, []),
        (
            [{"filename": "old.toml", "previous_filename": "slop_away.toml"}],
            [],
            None,
            ["label"],
        ),
        ([{"filename": "a.md"}], ["owner-approved"], 3001, ["complete"]),
    ]
)
def review_case(request):
    """GIVEN changed files WHEN checked THEN require complete review data."""
    files, labels, total, expected = request.param
    path = Path(__file__).resolve().parents[1] / ".github/workflows/owner_review.yml"
    step = yaml.safe_load(path.read_text())["jobs"]["owner-review"]["steps"][0]
    data = {"files": files, "labels": labels, "total": total}
    source = """
const data = JSON.parse(process.argv[1]);
const errors = [];
const github = {
  rest: {pulls: {get: async () => ({data: {
    changed_files: data.total ?? data.files.length,
    labels: data.labels.map(name => ({name})),
  }}), listFiles: {}}},
  paginate: async () => data.files,
};
const context = {repo: {owner: 'owner', repo: 'repo'}, issue: {number: 1}};
const core = {setFailed: message => errors.push(
  message.includes('complete') ? 'complete' : 'label')};
const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
"""
    source += (
        "new AsyncFunction('github', 'context', 'core', "
        + json.dumps(step["with"]["script"])
        + ")(github, context, core).then(() => console.log(JSON.stringify(errors)));"
    )
    return ["node", "-e", source, json.dumps(data)], expected


def test_review_gate(review_case):
    """GIVEN file and label data WHEN the check runs THEN enforce review."""
    arguments, expected = review_case
    result = subprocess.run(arguments, capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == expected
