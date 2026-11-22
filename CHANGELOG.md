# Changelog

All notable changes to this project will be documented in this file.

Headers will be commit hashes.

## [Unreleased]

### Added
- Add the Slice 6 baseline API, `--write-baseline`, per-file ignores,
  and JSON and GitHub annotation output.

### Decisions
- Store baseline data in `slop_away.baseline.json` at the project root.
  Use version 1 with a sorted, unique list of finding fingerprints.
  Reject malformed records and unsupported versions. A missing baseline
  is empty. An invalid baseline is an error during normal checks.
- Keep Python checks as raw finding APIs. The CLI removes matching
  baseline findings from its report and exit status. Baselines match
  code, project-relative path, and normalized context, without locations.
- `--write-baseline` replaces the snapshot with all findings from the
  selected files and exits zero. It does not merge old entries. It can
  replace an invalid baseline. With fix options, record remaining findings.
- Load a baseline before normal fix runs. Fixes still apply to baselined
  findings. Validate a new snapshot before replacing its file atomically.
- Normalize absolute Python check paths to project-relative paths so
  API and CLI fingerprints agree.
- Add all matching per-file ignores after profiles. Use project-relative
  glob matching, as for profiles. An ignore cannot enable a rule.
- JSON output is an array with every public finding field. Paths use POSIX
  separators. Empty JSON output is `[]`; empty text output has no lines.
- GitHub output uses error annotations with a rule-code title. Escape
  workflow command data and properties. Keep errors on stderr.
- No new dependencies are needed for this slice.

### Validation
- All 564 tests pass, including all Slice 6 feature scenarios.
- Ruff, mypy, Poetry lock checks, and hook manifest checks pass.
- Test baseline context matching, refreshes, malformed records, raw API
  findings, fix write protection, ignore precedence, package selectors,
  JSON fields, and GitHub annotation escaping.

## [67afae2cdb20a281f6e442ec60dda3d5f160c590]

### Added
- Add the Slice 5 fix API and the `--fix` and `--unsafe-fixes` options.

### Decisions
- Apply fixes only to visible source ranges. Preserve code, tables,
  front matter, URLs, link destinations, and HTML tag attributes.
- Safe fixes expand unambiguous contractions, reduce extra spaces within
  prose lines, and normalize spacing after valid ATX heading markers.
  Preserve indentation, line endings, and Markdown hard line breaks.
- Leave ambiguous contractions, possessives, passive voice, long sentences,
  and directives for review. Fixes do not infer missing meaning.
- Remove zero-width spaces, byte-order marks, and directional controls
  from visible prose and HTML comments when INJ004 is enabled. Preserve
  joiners that can change words or emoji. Instruction files get only
  hidden-character fixes.
- Unsafe fixes replace glossary synonyms, apply single external
  substitutions, and remove native filler phrases. Rule selectors and
  file profiles also control these fixes. Do not execute rule actions.
- Validate all selected files and package caches before file writes.
  Check the changed text again and report only the remaining findings.
  `--unsafe-fixes` includes safe fixes and does not require `--fix`.
- Remove hidden characters before other safe changes. Parse the result
  again before changing prose. Apply safe changes before unsafe changes.
  Reject conflicting edits,
  replacement cycles, and plans that need more than 20 passes. Do not
  return partially fixed text when a plan is invalid.
- Apply all selected external substitution matches. Leave replacements
  with alternative words for review. Finding limits control reports.
- Replace changed files atomically, one file at a time. Preserve file
  modes and line endings. Do not replace files whose text is unchanged.
  A later file-system write failure can leave earlier files changed.
- Whitespace and heading spacing have no rule codes. Apply these format
  changes to ordinary documents when fixing, including an empty selection.
- Keep native replacement capitalization. Keep external preferred text as
  written in its rule. Leave edits across source encodings or incomplete
  Markdown formatting for review.
- No new dependencies are needed for this slice.

### Validation
- All 496 tests pass, including all Slice 5 feature scenarios.
- Ruff, mypy, Poetry lock checks, and hook manifest checks pass.
- Test skipped content, safe-fix idempotence, rule selection, unsafe word
  swaps, conflicts, file modes, line endings, and batch input failures.

## [7cc97860e6dcca1c941096973082aa75a1802ce3]

### Added
- Add the Slice 4 package cache, `sync` command, Vale rule reader, and
  `slop_away-sync` pre-commit hook.

### Decisions
- Read ZIP packages from HTTPS URLs. Permit HTTP only for loopback test
  servers. Use the ZIP file name without its extension as the package name.
- Accept rules under `<name>/`, `styles/<name>/`, or
  `<name>/styles/<name>/`. Require exactly one rule directory.
- Store each package in `.slop_away/packages/<name>.zip`. Keep the source
  URL and content hashes in the cached package. Do not extract archives.
- Validate downloads and rule files before updating caches. Publish each
  cache file with an atomic replacement. Keep checks offline.
- Enable configured packages with native groups by default. An explicit
  `select` replaces that default. Package selectors match whole names.
- Support existence, substitution, occurrence, and sequence rules. Reject
  unsupported rule types, fields, and actions. Treat every finding as an
  error, including rules with Vale warning or suggestion levels.
- Apply project prose exclusions even to Vale `raw` scopes. Do not run
  package rules on instruction files. Require every configured package
  to have a valid cache, including packages excluded by rule selection.
- The inspected ai-tells v1.37.0 archive has 137 rules, rather than the
  134 rules listed in the design. All use the four planned rule types.
- Use PyYAML for rule data and `regex` for Unicode patterns and match
  time limits. Do not execute downloaded code or rule actions.
- Limit downloads to 16 MiB, expanded archives to 64 MiB, archives to
  4096 members, and rule files to 1 MiB. Limit sequence definitions to
  64 conditions and sequence searches to 100000 operations per sentence.
  Use a one-second limit for each regex search and a 30-second network
  timeout. Reject duplicate archive names, links, and unsafe paths.
- Require direct YAML children in the rule directory. Reject nested
  rules and duplicate rule names. Permit empty YAML documents around
  one rule mapping. Reject duplicate YAML keys and absent message values.
- Support text, raw, sentence, paragraph, heading, heading-level, and
  list scopes. Scope lists include positive matches and remove negative
  matches. Sequence rules use full-token text and word-class patterns.
- Report occurrence limits once per scope. Point to the first match,
  or the first visible character when the count is zero. Apply rule
  limits per document. Keep messages on one output line.
- Use scoped prose for finding fingerprints. Reuse parsed sentences
  across sequence rules in each document. Keep package caches out of Git.

### Validation
- All 426 tests pass, including all Slice 4 feature scenarios.
- Ruff, mypy, Poetry lock checks, and hook manifest checks pass.
- Sync the inspected ai-tells archive, stop its local download server,
  and check prose with its existence, substitution, and sequence rules.
  All 137 rule definitions pass validation.

## [5cfd638cb9aa2f4fdcdc50da0c9fc9bee6ae8f6b]

### Added
- Add the Slice 3 parser interface, STE001 to STE007, and the terminology
  glossary in the project config.
- Keep reference link identifiers out of prose only when their link
  definitions exist. Keep unresolved identifiers as visible text.

### Decisions
- Install the small English model as a pinned wheel dependency. Load the
  model only when STE checks need it. Checks do not download models.
- Set the supported Python range to `>=3.14,<3.15`, in line with the
  specified Python 3.14 runtime and spaCy dependency limits.
- Keep spaCy types behind the parser interface. Preserve source offsets
  when removing Markdown markers for language analysis.
- Use the model's word classes and dependency annotations for grammar
  decisions. Normalize curly apostrophes and line breaks for analysis.
- Use the 20-word limit for numbered steps and sentences that start with
  an imperative verb. Use the 25-word limit for other sentences.
- Count sentences within each Markdown paragraph or list paragraph.
  Do not apply the paragraph sentence limit to headings.
- Check simple passive constructions with STE003. Check perfect and
  progressive constructions with STE005. Permit simple modal forms.
- Distinguish possessive apostrophes from contracted auxiliary verbs.
- Count consecutive common and proper nouns for STE006. Punctuation and
  other parts of speech end a noun cluster.
- Match glossary synonyms as complete terms without regard to case.
  Require explicit glossary entries for plural and other word forms.
- Reject empty, duplicate, and conflicting glossary terms. Keep the
  glossary global; profiles can select or ignore STE007 for a file.

### Validation
- All 336 tests pass on Python 3.14.4, including every Slice 3 scenario.
- Tests check exact sentence and paragraph limits, grammar cases, source
  locations, glossary validation, rule selection, and instruction files.
- A fresh CLI process runs the installed model with network access
  blocked. spaCy 3.8.18 and model `en_core_web_sm` 3.8.0 are installed.
- Pre-commit, Python style and type checks, and Poetry validation pass.
  The wheel and source archive build.
- Move T016 to T019 to Done. Keep the protected document set unchanged.

## [42ca5dc67b9e0efd7e62fe5b1808524cd245d2b3]

### Added
- Add the Slice 2 phrase, word budget, repeated sentence, and readability
  checks. Add rule settings for files that match a profile glob.

### Decisions
- Apply matching profiles in config order. The last value for a setting
  wins. A profile replaces the global value for that setting.
- Match profile globs against project-relative paths. Require a finite
  grade limit of zero or more and an integer word budget of zero or more.
- Count visible prose words for file budgets. Count headings and lists,
  but omit code, front matter, tables, URLs, and HTML comments.
- Count contractions, words with hyphens, and decimal numbers as single
  words. Do not count numbers that have no letters in readability scores.
- Split sentences at terminal punctuation or the end of a prose block.
  Keep common English abbreviations and initialisms within a sentence.
- Start with the three filler phrases and three hedge phrases in the
  VRB feature examples. Match case changes and text on multiple lines.
- Report repeated sentences after their first occurrence. Compare case
  and whitespace only, and require at least eight words. For checks
  across files, only files with VRB005 enabled take part. Sort input
  paths before checking them.
- Score paragraph prose within each h2 section. End a section at the next
  h1 or h2 heading. Do not score headings, lists, or empty sections.
- Use syllapy for offline English syllable counts. Compare unrounded
  Flesch-Kincaid grades with the configured limit.

### Validation
- All 219 tests pass on Python 3.14.4, including every Slice 2 scenario.
- Tests check exact limits, profile replacement and order, excluded
  content, section boundaries, source locations, and repeated sentences
  across selected files.
- Pre-commit, Python style and type checks, and Poetry validation pass.
  The wheel and source archive build.
- Move T013 to T015 to Done. Keep the protected document set unchanged.

## [000c2f054bf04a7f01a981b0f3b91b3f0d12f7b6]

### Added
- Add the Slice 1 public API, config loading, file selection, Markdown
  extraction, injection checks, and text and agent output.
- Add feature tests and a Git test tool that checks real commits with
  the installed pre-commit hook.

### Decisions
- Use markdown-it-py with link support and the front matter plugin.
  Use pathspec for Git ignore patterns. Checks need no network access.
- Find CLI settings from the nearest config or Git directory above the
  command directory. With no paths, check the command directory.
- Resolve API input paths from `config.root`. Return sorted, unique
  absolute paths from `select_files`. Findings use project-relative paths.
- Apply exclusions to explicit paths too. Skip symbolic links. Reject
  paths outside the project and input patterns with no matches.
- Read nested `.gitignore` files. Prune excluded directories.
- Accept the Slice 1 config keys only. Add later settings with their
  slices. Check rule selectors against the native rule code list.
- Treat checked boxes, explicit status fields, and status labels in
  parentheses as action status. Require valid dates in `YYYY-MM-DD` form.
- Check Unicode format characters as hidden text. Check HTML comments
  with INJ rules only. Do not check code examples as comments.
- Build each fingerprint from the rule code, project path, and SHA-256
  hash of the sentence text after case and whitespace normalization.
- In Git tests, use the installed command with a local copy of the hook
  manifest. Change its language to `system` to keep tests offline.
- Return exit code 2 for internal errors and log the error on stderr.

### Validation
- All 127 tests pass on Python 3.14.4, including every Slice 1 scenario.
- Real Git commits pass for clean Markdown and fail for findings.
- Pre-commit, Poetry metadata and lock checks, Python style checks, and
  type checks pass. The wheel and source archive build.
- Move T006 to T012 to Done. Keep the protected document set unchanged.

## [8a960d2f7424f4a72fca7bc28784a5b235317822]

### Added
- Add the Slice 0 package in `src/slop_away` and tests in `tests`.
- Add the version command, API and CLI test tools, and test directories.
- Add Poetry dependencies, a hook manifest, and CI checks.
- Add tests for API arguments and errors, command output and directory,
  empty commands, and the installed package version.
- Mark the package as typed so callers can check its public type hints.

### Decisions
- Use package version `0.1.0` for the first development build. Read the
  version from the installed package metadata.
- Use the standard Python command parser. With no arguments, print help
  and exit 0. The `check` command starts in Slice 1.
- Bind feature scenarios as each slice supplies their behavior. Slice 0
  binds `@cli_01`; the other feature files stay unchanged.
- Run CLI tests in a temporary project. Use the test environment's
  command directory and a 30-second time limit. Do not use a shell.
- Store expected corpus codes in `tests/corpus/expected.json`. Each key
  is a path relative to `tests/corpus/bad/`. Each value is a list of exact
  rule codes. Start with an empty object until corpus documents are added.
- Keep empty test directories with `.gitkeep` files.
- Add pre-commit as a development dependency. Local hooks check Poetry
  metadata, the hook manifest, and tests. CI runs these hooks on Python
  3.14. The lint hook becomes usable with the Slice 1 `check` command.
- Use HTTPS ZIP package URLs for future package downloads. Allow HTTP
  only for local test servers. Define package layout tests in Slice 4.
- Safe hidden-text fixes will remove invisible characters only.
  Directives in HTML comments will need manual correction.

### Validation
- Python 3.14.4 runs all eight tests. The `@cli_01` scenario passes with
  pytest-bdd 9.0.1. The installed command prints `0.1.0`.
- Poetry metadata and lock checks pass. The pre-commit checks pass.
- The wheel and source archive build. Python style and type checks pass.
- Move T001 to T005 to Done. Keep the protected document set unchanged.

## [1.0.0]

### Added
- Initial public release.
- Added core project functionality and usage documentation.
