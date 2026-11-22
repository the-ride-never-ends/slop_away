# Changelog

All notable changes to this project will be documented in this file.

Headers will be commit hashes.

## [Unreleased]

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
