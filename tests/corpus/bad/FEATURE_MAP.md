# slop_away feature map

Maps each Phase 1 feature to its feature file, scenario tags, test harness,
properties, and differential tests. The scenario titles here are short
names. The feature files hold the full Given, When, Then text.

Scenario tags are lowercase with an underscore, such as `@inj_03`. Tag
numbers count scenarios within a file. They do not match rule codes.

## Harnesses

| Harness | What it does |
|---------|--------------|
| api | Calls the public Python API in the test process. Checks return values and raised exceptions. |
| cli | Runs `slop_away` as a subprocess on files in a temporary directory. Checks exit code, stdout, stderr, and files written. |
| git | Creates a temporary git repo with pre-commit installed. Runs `git commit` and checks whether it succeeds. |
| hook | Runs a hook script with hook-event JSON on stdin. Checks exit code and stderr. |
| corpus | Calls `check_files` on every corpus document and compares codes to the expected list. |

## Public API

The api harness calls these callables. They are the package's public contract.

| Callable | Returns | Raises |
|----------|---------|--------|
| `load_config(root)` | `Config` | `ConfigError` |
| `Config()` | The default config | |
| `select_files(paths, config)` | `list[Path]` | |
| `check_text(text, path, config)` | `list[Finding]` | `PackageError` |
| `check_files(paths, config)` | `list[Finding]` | `PackageError` |
| `check_message(text, config)` | `list[Finding]` | `PackageError` |
| `apply_fixes(text, path, config, unsafe)` | `str` | |
| `Baseline.from_findings(findings)` | `Baseline` | |
| `Baseline.matches(finding)` | `bool` | |

`Finding` fields: `code`, `path`, `line`, `column`, `message`, `hint`,
`fingerprint`. The fingerprint is computed when the check runs, from the rule
code, the file path, and the normalized sentence or section text.

## Rule codes

| Code | Rule |
|------|------|
| INJ001 | Directive addressed to the reader |
| INJ002 | Role marker |
| INJ003 | Action item without a status or date |
| INJ004 | Hidden text: directives in HTML comments, invisible characters |
| VRB001 | Filler phrase |
| VRB002 | Hedge phrase |
| VRB003 | Word budget exceeded |
| VRB004 | Sentence of 8 or more words repeated within a document, after normalizing case and whitespace |
| VRB005 | Sentence of 8 or more words repeated across documents, after normalizing case and whitespace |
| RDB001 | h2 section above the grade limit |
| STE001 | Sentence too long: 20 words in procedures, 25 in descriptions |
| STE002 | Paragraph over 6 sentences |
| STE003 | Passive voice |
| STE004 | Contraction |
| STE005 | Tense that is not simple |
| STE006 | Noun cluster over 3 nouns |
| STE007 | Banned synonym from the glossary |
| MSG001 | Commit subject over 72 characters |
| MSG002 | Commit subject not in imperative mood |
| MSG003 | Commit subject with a trailing period |
| MSG004 | Commit body over its word budget |
| `package.Rule` | Rule from an external Vale package, such as `ai-tells.Dash` |

## Config keys

In pyproject.toml, the same keys go under `[tool.slop_away]`.

| Key | Type | Default |
|-----|------|---------|
| `include` | List of globs | `["**/*.md"]` |
| `exclude` | List of paths or globs | `[".git", ".venv", "node_modules", "build", "dist"]` |
| `extend-exclude` | List of paths or globs | `[]` |
| `select` | List of codes, code prefixes, or package names | `["INJ", "VRB", "RDB", "STE", "MSG"]` plus each package in `packages`. An explicit value replaces the default. |
| `ignore` | List of codes, code prefixes, or package names | `[]` |
| `instruction-files` | List of file names | `["AGENTS.md", "CLAUDE.md", "SKILL.md"]` |
| `max-grade` | Number | `10` |
| `word-budget` | Integer | None |
| `commit-body-budget` | Integer | `150` |
| `packages` | List of package URLs | `[]` |
| `glossary` | Table: preferred term to a list of banned synonyms | `{}` |
| `per-file-ignores` | Table: glob to a list of codes | `{}` |
| `profiles` | Table: glob to settings (`select`, `ignore`, `max-grade`, `word-budget`) | `{}` |

## Features

| ID  | Feature | File | Harness | Slice |
|-----|---------|------|---------|-------|
| F01 | CLI basics | cli.feature | cli | 1 |
| F02 | Config | config.feature | api | 1, 2, 6 |
| F03 | File selection | selection.feature | api | 1 |
| F04 | Markdown extraction | markdown.feature | api | 1, 2 |
| F05 | Output formats | output.feature | cli | 1, 6 |
| F06 | INJ rules | inj.feature | api | 1 |
| F07 | VRB rules | vrb.feature | api | 2 |
| F08 | RDB rule | rdb.feature | api | 2 |
| F09 | STE rules | ste.feature | api | 3 |
| F10 | Package sync | sync.feature | cli | 4 |
| F11 | Vale-compatible rules | ait.feature | api | 4 |
| F12 | Fixes | fix.feature | api, cli | 5 |
| F13 | Baseline | baseline.feature | api, cli | 6 |
| F14 | Commit messages | msg.feature | api | 7 |
| F15 | Pre-commit hooks | precommit.feature | git | 1, 4, 7 |
| F16 | Agent hooks | hooks.feature | hook | 8 |
| F17 | Init | init.feature | cli | 8 |
| F18 | Corpus | corpus.feature | corpus | 9 |

## Scenarios

### F01 CLI basics

| Tag | Scenario | Slice |
|-----|----------|-------|
| @cli_01 | `--version` prints the version and exits 0 | 1 |
| @cli_02 | A clean file exits 0 with no output | 1 |
| @cli_03 | A file with findings exits 1 | 1 |
| @cli_04 | An unknown option exits 2 | 1 |
| @cli_05 | A path that does not exist exits 2 and names the path | 1 |

### F02 Config

| Tag | Scenario | Slice |
|-----|----------|-------|
| @config_01 | Settings are read from `[tool.slop_away]` in pyproject.toml | 1 |
| @config_02 | Settings are read from slop_away.toml | 1 |
| @config_03 | When both sources set config, slop_away.toml is used and pyproject.toml is ignored | 1 |
| @config_04 | An unknown key exits 2 and names the key | 1 |
| @config_05 | An invalid value exits 2 and names the key | 1 |
| @config_06 | `select` limits the run to the listed rules | 1 |
| @config_07 | `ignore` removes the listed rules | 1 |
| @config_08 | A profile changes rule settings for files matching its glob | 2 |
| @config_09 | `per-file-ignores` removes rules for matching files | 6 |
| @config_10 | An inline suppression comment has no effect | 6 |
| @config_11 | A pyproject.toml without a `[tool.slop_away]` section is ignored | 1 |

### F03 File selection

| Tag | Scenario | Slice |
|-----|----------|-------|
| @selection_01 | A recursive glob such as `docs/**/*.md` selects nested files | 1 |
| @selection_02 | A directory path selects the `.md` files under it | 1 |
| @selection_03 | `exclude` removes matching files | 1 |
| @selection_04 | `extend-exclude` adds to the default excludes | 1 |
| @selection_05 | Files listed in .gitignore are skipped | 1 |
| @selection_06 | Files that are not `.md` are skipped | 1 |

### F04 Markdown extraction

| Tag | Scenario | Slice |
|-----|----------|-------|
| @markdown_01 | Text in a fenced code block produces no prose findings | 1 |
| @markdown_02 | Inline code produces no prose findings | 1 |
| @markdown_03 | Front matter produces no prose findings | 1 |
| @markdown_04 | A bare URL produces no prose findings | 1 |
| @markdown_05 | Table cells produce no prose findings | 1 |
| @markdown_06 | An HTML comment is skipped by prose rules | 2 |
| @markdown_07 | Link text is checked as prose | 1 |

### F05 Output formats

| Tag | Scenario | Slice |
|-----|----------|-------|
| @output_01 | `text` format shows path, line, column, code, and message | 1 |
| @output_02 | `agent` format prints one line per finding: code, location, message, fix hint | 1 |
| @output_03 | Findings go to stdout and nothing else does | 1 |
| @output_04 | `json` format prints a JSON array of findings | 6 |
| @output_05 | `github` format prints GitHub Actions annotation lines | 6 |

### F06 INJ rules

| Tag | Scenario | Slice |
|-----|----------|-------|
| @inj_01 | INJ001: a directive addressed to the reader-agent is flagged | 1 |
| @inj_02 | INJ001: an agent instruction file is exempt | 1 |
| @inj_03 | INJ002: a role marker such as "SYSTEM:" is flagged | 1 |
| @inj_04 | INJ003: an action item without a status or date is flagged | 1 |
| @inj_05 | INJ003: an action item with a status or a date passes | 1 |
| @inj_06 | INJ004: a directive inside an HTML comment is flagged | 1 |
| @inj_07 | INJ004: zero-width or other invisible characters are flagged | 1 |
| @inj_08 | INJ002 to INJ004 apply to agent instruction files | 1 |

### F07 VRB rules

| Tag | Scenario | Slice |
|-----|----------|-------|
| @vrb_01 | A filler phrase is flagged | 2 |
| @vrb_02 | A hedge phrase is flagged | 2 |
| @vrb_03 | A file over its glob's word budget is flagged | 2 |
| @vrb_04 | A point repeated within one document is flagged | 2 |
| @vrb_05 | A point repeated across documents is flagged | 2 |
| @vrb_06 | A repeated sentence under 8 words passes | 2 |

### F08 RDB rule

| Tag | Scenario | Slice |
|-----|----------|-------|
| @rdb_01 | An h2 section above the grade limit is flagged | 2 |
| @rdb_02 | An h2 section at or below the limit passes | 2 |
| @rdb_03 | A profile changes the grade limit | 2 |
| @rdb_04 | Lists, tables, and code do not count toward the score | 2 |

### F09 STE rules

| Tag | Scenario | Slice |
|-----|----------|-------|
| @ste_01 | STE001: a procedure sentence over 20 words is flagged | 3 |
| @ste_02 | STE001: a description sentence of 21 to 25 words passes | 3 |
| @ste_03 | STE001: a description sentence over 25 words is flagged | 3 |
| @ste_04 | STE002: a paragraph over 6 sentences is flagged | 3 |
| @ste_05 | STE003: a passive sentence is flagged | 3 |
| @ste_06 | STE004: a contraction is flagged | 3 |
| @ste_07 | STE005: a sentence not in a simple tense is flagged | 3 |
| @ste_08 | STE006: a noun cluster over 3 nouns is flagged | 3 |
| @ste_09 | STE007: a banned synonym from the glossary is flagged | 3 |

### F10 Package sync

| Tag | Scenario | Slice |
|-----|----------|-------|
| @sync_01 | `sync` downloads configured packages into the cache | 4 |
| @sync_02 | `check` exits 2 and names a configured package that is not synced | 4 |
| @sync_03 | `check` runs with no network access after `sync` | 4 |

### F11 Vale-compatible rules

| Tag | Scenario | Slice |
|-----|----------|-------|
| @ait_01 | An existence rule flags its tokens | 4 |
| @ait_02 | A substitution rule flags its terms and names the replacement | 4 |
| @ait_03 | An occurrence rule flags a count over its limit | 4 |
| @ait_04 | A sequence rule flags its part-of-speech pattern | 4 |
| @ait_05 | External findings use the package's rule name | 4 |
| @ait_06 | A synced package that the config does not list does not run | 4 |
| @ait_07 | An explicit `select` that leaves out the package excludes its rules | 4 |
| @ait_08 | `ignore` removes package rules by package name or rule code | 4 |

### F12 Fixes

| Tag | Scenario | Slice |
|-----|----------|-------|
| @fix_01 | `--fix` applies safe fixes | 5 |
| @fix_02 | `--fix` does not apply unsafe fixes | 5 |
| @fix_03 | `--fix --unsafe-fixes` applies unsafe fixes | 5 |
| @fix_04 | Findings with no fix remain after `--fix` | 5 |
| @fix_05 | A second `--fix` run changes nothing | 5 |
| @fix_06 | `check --fix` rewrites the file on disk | 5 |

### F13 Baseline

| Tag | Scenario | Slice |
|-----|----------|-------|
| @baseline_01 | `check --write-baseline` writes slop_away.baseline.json | 6 |
| @baseline_02 | Findings in the baseline do not fail the run | 6 |
| @baseline_03 | A finding not in the baseline fails the run | 6 |
| @baseline_04 | A baselined finding still matches after its lines move | 6 |
| @baseline_05 | Editing a baselined sentence makes its findings new | 6 |

### F14 Commit messages

| Tag | Scenario | Slice |
|-----|----------|-------|
| @msg_01 | A subject over 72 characters is flagged | 7 |
| @msg_02 | A subject not in imperative mood is flagged | 7 |
| @msg_03 | A subject with a trailing period is flagged | 7 |
| @msg_04 | A body over its word budget is flagged | 7 |
| @msg_05 | Trailers such as Co-Authored-By are skipped | 7 |
| @msg_06 | INJ001 does not apply to commit messages | 7 |

### F15 Pre-commit hooks

| Tag | Scenario | Slice |
|-----|----------|-------|
| @precommit_01 | The `slop_away` hook blocks a commit with findings | 1 |
| @precommit_02 | The `slop_away` hook allows a clean commit | 1 |
| @precommit_03 | The `slop_away-sync` hook syncs configured packages | 4 |
| @precommit_04 | The `slop_away-msg` hook blocks a commit message with findings | 7 |

### F16 Agent hooks

| Tag | Scenario | Slice |
|-----|----------|-------|
| @hooks_01 | PostToolUse on an edited `.md` file with findings exits 2 with agent-format findings on stderr | 8 |
| @hooks_02 | PostToolUse on a clean file exits 0 | 8 |
| @hooks_03 | PostToolUse on a file that is not `.md` exits 0 | 8 |
| @hooks_04 | Stop with findings remaining exits 2 | 8 |
| @hooks_05 | Stop with `stop_hook_active` true exits 0 | 8 |
| @hooks_06 | PreToolUse blocks `git commit --no-verify` | 8 |
| @hooks_07 | PreToolUse allows `git commit` without `--no-verify` | 8 |

### F17 Init

| Tag | Scenario | Slice |
|-----|----------|-------|
| @init_01 | `init` writes the config, pre-commit entries, CI workflow, and hook scripts and settings | 8 |
| @init_02 | Each skip flag leaves out its part | 8 |
| @init_03 | An existing slop_away.toml exits 2, names the file, and writes nothing | 8 |
| @init_04 | `init` does not write CODEOWNERS | 8 |
| @init_05 | `init` adds its hooks to an existing .pre-commit-config.yaml and keeps its contents | 8 |
| @init_06 | `init` adds its hook entries to an existing .claude/settings.json and keeps its contents | 8 |
| @init_07 | `init` adds `.slop_away/` to an existing .gitignore and keeps its contents | 8 |

### F18 Corpus

| Tag | Scenario | Slice |
|-----|----------|-------|
| @corpus_01 | Each bad document produces exactly its expected codes | 9 |
| @corpus_02 | Each fixed document produces no findings | 9 |
| @corpus_03 | Each good document produces no findings | 9 |
| @corpus_04 | A change in findings fails and lists each document that gained or lost a code | 9 |
| @corpus_05 | The slop_away repo's own docs produce no findings | 9 |

## Properties

Hypothesis tests in `tests/properties/`. Slice 9.

| ID | Property | Features |
|----|----------|----------|
| P1 | Applying safe fixes twice gives the same text as applying them once | F12 |
| P2 | A baseline fingerprint matches after lines are inserted above the finding | F13 |
| P3 | Changing text inside a fenced code block never changes the findings | F04 |
| P4 | Any input either produces findings and exit 0 or 1, or exits 2. The process never crashes | F01, F04 |
| P5 | Findings are the same for any order of the input files | F05 |

## Differential tests

Tests in `tests/differential/`. Slice 9 unless noted.

| ID | Compares | Tolerance | Features |
|----|----------|-----------|----------|
| X1 | RDB Flesch-Kincaid grade against textstat on the corpus | 0.5 grade | F08 |
| X2 | Vale-compatible rule findings against Vale on the corpus | Same codes and lines | F11 |
| X3 | Current build against the previous release on the corpus | Same findings | Phase 2 |
