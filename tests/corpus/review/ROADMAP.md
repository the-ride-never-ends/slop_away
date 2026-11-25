# slop_away roadmap

Phase 1 is the MVP, in MVP.md. This file covers Phases 2 to 5 and the
items without a schedule. Each phase ends when its feature files pass.

## Phase 2: Codex, CI, and speed

- Codex hooks: PostToolUse, Stop, and PreToolUse, matching the Claude Code
  hooks from Phase 1. `init` writes them to `.codex/hooks.json`.
  Codex loads project hooks only after the user trusts the project's `.codex/` layer.
- GitHub Action: runs `slop_away check` on pull requests with the `github`
  output format.
- PR description checks: AIT, VRB, INJ002 to INJ004, and a word budget.
  Run by the GitHub Action.
- Benchmarking with pytest-benchmark. Target: under 2 seconds to check one
  typical Markdown file.
- If checks miss the target: a background process that keeps the
  spaCy model in memory.
- Version-to-version differential tests: the current build against the
  previous release, on the corpus.

Done when: `codex.feature`, `action.feature`, and `pr.feature` pass, and the
benchmark suite meets the target.

## Phase 3: Code text and one report

- Prose rules on Python docstrings and code comments.
- Docstring format stays with ruff's D rules (Google convention).
- One combined report: slop_away runs lychee and rumdl and merges their
  findings into its own output formats and exit code.

Done when: `docstring.feature`, `comment.feature`, and `report.feature` pass.

## Phase 4: Native Windows

- Replace the bash and `jq` hook scripts with a version that runs on native
  Windows.
- Windows in the CI matrix.
- Windows path handling in config globs, baseline fingerprints, and output.

Done when: the full test suite passes on Windows in CI.

## Phase 5: Full ASD-STE100

- An opt-in `ste-strict` profile with every ASD-STE100 writing rule.
- Approved-word checking against a dictionary file the user supplies.
  slop_away does not ship the dictionary.
- Project technical nouns and technical verbs from config.

Done when: `ste_strict.feature` passes.

## Not scheduled

- SARIF output.
- Throat-clearing detection in VRB.
- Vale rule types beyond existence, substitution, occurrence, and sequence.
- `.rst` and `.txt` input.
- MkDocs and MDX Markdown flavors.
- Agent instruction files under the full prose rule set.
- A Stop-hook retry counter allowing more than one pass.
- Conventional Commits checks in MSG.
- INJ001 on PR descriptions, as an opt-in setting.
- Publishing to PyPI.
