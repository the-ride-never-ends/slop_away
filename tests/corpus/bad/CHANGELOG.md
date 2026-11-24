# Changelog

All notable changes to this project will be documented in this file.

Headers will be commit hashes.

## [Unreleased]

### Added
- Add the Slice 8 project initializer and packaged Bash hooks for
  PostToolUse, Stop, and PreToolUse. Add the `guard` command for shell input.

### Decisions
- `init` targets the current directory. It does not install tools, Git hooks,
  or packages, and it does not download data. Bash and jq are required to
  run the generated Claude Code hooks. No Python dependencies are added.
- Validate all planned targets and merge data before writes. Reject symlink
  targets and parents. Skip flags omit their targets from validation.
  Keep `.gitignore` setup even when all four parts are skipped.
- Preserve existing configuration values. YAML and JSON merge files are
  serialized again, so YAML comments and formatting are not preserved.
  Keep existing repository revisions and hook options. Add missing hook IDs
  and both Git install stages. Do not write CODEOWNERS.
- Preserve existing Claude settings and event hooks. Add command hooks for
  Write and Edit, Stop, and Bash. Use CLAUDE_PROJECT_DIR for script paths
  and check scope. Reject malformed hook input with exit code 2.
- The post-edit hook checks one lowercase `.md` path relative to event cwd.
  Stop checks the project once and permits the next stop_hook_active pass.
  Map findings and check errors to hook exit code 2, with feedback on stderr.
- Inspect literal shell arguments without executing them. Detect commit
  skip flags, including short option groups, Git global options, wrappers,
  and literal nested shell commands. Skip message values and path operands.
  This guard does not evaluate shell variables, substitutions, or aliases.
  Limit nested command strings to four levels.
- Pin generated slop_away checks to the completed Slice 7 commit
  `627bbfcafa1f1de06ca05a5786235c1fc7501b20`, lychee to `lychee-v0.24.2`,
  and rumdl to `v0.2.78`. The generated agent scripts use the installed
  slop_away command. CI installs Python 3.14 and runs pre-commit on all files.
- Write each file atomically and retain existing modes. Create hook scripts
  with mode 0755 and other new files with mode 0644. A later file-system
  failure can leave earlier files changed.

### Validation
- All 739 tests pass, including all 33 Slice 8 feature cases.
- Ruff, mypy, Poetry lock checks, Bash syntax checks, and pre-commit config
  and manifest validation pass.
- Test conflict preflight, merge values, YAML aliases, file modes, literal
  paths, malformed events, stop-hook re-entry, and command non-execution.
- Build the wheel and import it directly. All five templates are packaged,
  and init generates all eight target files with a resolved CI revision.
