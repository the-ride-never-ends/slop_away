# slop_away MVP

The MVP is Phase 1. It ships in slices. Each slice works end to end and
leaves the tool usable. The feature files under `tests/features/` define
the behavior. FEATURE_MAP.md lists which scenarios belong to each slice. A
slice is done when its scenarios pass.

Later phases are in ROADMAP.md.

## Slice 0: Project skeleton

- Poetry project, Python 3.14, package `slop_away`, console command `slop_away`.
- Dev dependencies: pytest, pytest-bdd, Hypothesis, pytest-cov.
- Corpus folders: `tests/corpus/bad/`, `tests/corpus/fixed/`, `tests/corpus/good/`.
  Each bad document has a list of its expected rule codes.
- `.pre-commit-hooks.yaml`.
- GitHub Actions workflow that runs `pre-commit run --all-files`.

Done when: `slop_away --version` prints the version, and `pytest` runs in CI.

## Slice 1: Injection checks on Markdown

- `slop_away check [PATHS]`.
- Config from `[tool.slop_away]` in `pyproject.toml`, or from `slop_away.toml`.
  Unknown keys and invalid values are errors.
- File selection: `include`, `exclude`, `extend-exclude`, recursive globs, `.gitignore`.
- GitHub-flavored Markdown parsing. Prose rules skip code blocks, inline code,
  front matter, URLs, and tables. HTML comments go to the INJ rules only.
  Link text counts as prose.
- Rules INJ001 to INJ004. Instruction files get INJ002 to INJ004 only.
- `select` and `ignore`.
- Output formats: `text` and `agent`.
- Exit codes: 0 clean, 1 findings, 2 usage or internal error.
- Pre-commit hook: `slop_away`.

Done when: the Slice 1 scenarios in FEATURE_MAP.md pass.

## Slice 2: Verbosity and readability

- VRB rules: filler and hedge phrases, word budgets per glob, repeated content.
  Repeated content: sentences of at least 8 words that match after
  normalizing case and whitespace.
- RDB rule: Flesch-Kincaid grade per h2 section. Default limit: grade 10.
- Profiles: rule settings per glob.

Done when: the Slice 2 scenarios in FEATURE_MAP.md pass.

## Slice 3: STE subset

- spaCy small English model behind a parser interface. The model wheel is a
  pinned dependency.
- Rules STE001 to STE007:
  - STE001 sentence length: at most 20 words in procedures, 25 in descriptions
  - STE002 at most 6 sentences per paragraph
  - STE003 active voice
  - STE004 no contractions
  - STE005 simple tenses
  - STE006 noun clusters of at most 3 nouns
  - STE007 one term per meaning, from the config glossary
- Procedures are numbered list steps and sentences that start with an
  imperative verb.

Done when: the Slice 3 scenarios in FEATURE_MAP.md pass.

## Slice 4: Vale-compatible rules

- `slop_away sync` downloads the packages listed in the config into the cache
  at `.slop_away/packages/` in the repo root.
- Rule types read: existence, substitution, occurrence, sequence.
- External rules keep their own names, such as `ai-tells.Dash`.
- Rules from packages in `packages` run by default. An explicit `select`
  replaces the default. `select` and `ignore` accept package names and rule
  codes.
- `check` exits 2 and names the package when a configured package is not synced.
- Pre-commit hook: `slop_away-sync`.

Done when: the Slice 4 scenarios in FEATURE_MAP.md pass.

## Slice 5: Fixes

- `--fix` applies safe fixes: whitespace, Markdown structure, hidden-text
  removal, contraction expansion.
- `--unsafe-fixes` also applies word swaps and filler deletion.
- Sentence splits, passive to active, and directive removal have no fix.

Done when: the Slice 5 scenarios in FEATURE_MAP.md pass.

## Slice 6: Adoption

- Baseline file `slop_away.baseline.json` at the repo root. Fingerprint:
  rule code, file path, hash of the normalized sentence or section text.
  Each finding carries its fingerprint.
  `slop_away check --write-baseline` writes the file. `check` reads it when present.
- `per-file-ignores` in the config. No inline suppression.
- Output formats: `json` and `github`.

Done when: the Slice 6 scenarios in FEATURE_MAP.md pass.

## Slice 7: Commit messages

- MSG rules: subject of at most 72 characters, imperative mood, no trailing
  period, body word budget. Also AIT, INJ002 to INJ004, and the VRB filler
  rules. Trailers are skipped.
- Entry point: `slop_away check --commit-msg PATH`.
- Pre-commit hook at the commit-msg stage: `slop_away-msg`.

Done when: the Slice 7 scenarios in FEATURE_MAP.md pass.

## Slice 8: Agent hooks and init

- Bash hook scripts shipped with slop_away, one per hook event, using `jq`:
  - PostToolUse on Write and Edit: check the edited file. On findings, print
    them to stderr in the agent format and exit 2.
  - Stop: block finishing while findings remain, for one pass, using
    `stop_hook_active`.
  - PreToolUse on Bash: block `git commit --no-verify`.
- `slop_away init` writes:
  - the config
  - the pre-commit entries: slop_away, slop_away-sync, slop_away-msg, lychee, rumdl
  - the CI workflow that runs `pre-commit run --all-files`
  - the hook scripts under `.claude/hooks/` and their entries in
    `.claude/settings.json`
  - a `.slop_away/` entry in `.gitignore`
- `init` adds its entries to an existing `.pre-commit-config.yaml`,
  `.claude/settings.json`, and `.gitignore`. Any other existing target file
  stops `init` with exit code 2 before it writes anything.
- Flags skip each part. `init` does not write CODEOWNERS.

Done when: the Slice 8 scenarios in FEATURE_MAP.md pass.

## Slice 9: Validation

- Corpus suite: each bad document produces exactly its expected codes.
  Fixed and good documents produce none.
- Property tests:
  - Safe fixes are idempotent.
  - Baseline fingerprints survive line moves.
  - Code-block content never changes findings.
  - The parser never crashes. It succeeds or exits 2.
  - Findings do not depend on file order.
- Differential tests:
  - RDB scores against textstat, within 0.5 grade.
  - Vale-compatible rules against Vale, on the corpus.
- Self-check: the slop_away repo's own docs and commit messages pass.
- The repo's own baseline holds only findings in existing CHANGELOG entries.
- Auto-fix results go to `tests/corpus/drafts/`. The corpus keeps a
  50-line excerpt of the CHANGELOG as a bad document.
- A CI check fails when a pull request changes the config, the baseline,
  CODEOWNERS, or `.github/` without the `owner-approved` label.
- With no `commit-body-budget` in the config, the body budget is 150
  words. Profiles do not set `commit-body-budget`.

Done when: the Slice 9 scenarios, properties, and differential tests in
FEATURE_MAP.md pass.

## Slice 10: Generated tests

- Tier 1, for the mechanical rules: STE001, STE002, STE004, STE007,
  VRB001 to VRB005, INJ002, INJ003, INJ004 for invisible characters,
  MSG001, MSG003, and MSG004.
  - A planted defect gives exactly its code at its line, and no other
    new finding.
  - An edit that keeps the meaning gives the same findings.
- Tier 2 covers the rules that depend on the parser. These are STE003,
  STE005, STE006, MSG002, INJ001, procedure detection, and INJ004 for
  directives in comments.
  - Templates build sentences with known labels. Each rule meets its
    minimum precision and recall on them.
  - Stanza parses the external documents. Each rule meets its minimum
    precision and recall against labels from that parse.
  - A ratchet file records the measured values. CI fails when a value
    drops.
  - Stanza is in its own Poetry dependency group. Its CI job runs on
    pull requests to `main` and once a week.
- External documents: 30 files with MIT, Apache-2.0, or BSD licenses,
  from public GitHub repos with at least 20 stars. A script draws them
  at random with a recorded seed. `tests/corpus/external/sources.json`
  pins the repo, commit, path, and license of each file.
- The draw rejects a file with fewer than 150 words of prose. It also
  rejects a file where code, tables, or bare links fill more than half
  of the lines. After a rejection, it draws again with the next seed value.

| Type | Files | From 2021 or earlier | From 2023 or later |
|------|-------|----------------------|--------------------|
| README | 6 | 3 | 3 |
| Contributor or developer guide | 4 | 2 | 2 |
| CHANGELOG | 4 | 2 | 2 |
| TODO or roadmap | 4 | 2 | 2 |
| Design doc or ADR | 4 | 2 | 2 |
| Agent instruction file | 4 | 0 | 4 |
| Tutorial or how-to | 4 | 2 | 2 |

Done when: the Slice 10 properties and accuracy tests in FEATURE_MAP.md
pass. Each minimum comes from the owner.
