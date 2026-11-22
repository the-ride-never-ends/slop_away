# slop_away TODO

Item format: checkbox, ID, date added, description, scenario tags. An
optional status of `doing` or `blocked` follows the tags. Scenario tags
refer to FEATURE_MAP.md.

## Slice 0: Project skeleton

## Slice 1: Injection checks on Markdown


## Slice 2: Verbosity and readability


## Slice 3: STE subset


## Slice 4: Vale-compatible rules


## Slice 5: Fixes


## Slice 6: Adoption

- [ ] T025 2026-11-21: Baseline file and `check --write-baseline`. Tags: @baseline_01 @baseline_02 @baseline_03 @baseline_04 @baseline_05
- [ ] T026 2026-11-21: `per-file-ignores`, with inline suppression comments having no effect. Tags: @config_09 @config_10
- [ ] T027 2026-11-21: `json` and `github` output formats. Tags: @output_04 @output_05

## Slice 7: Commit messages

- [ ] T028 2026-11-21: MSG rules and `check --commit-msg PATH`. Tags: @msg_01 @msg_02 @msg_03 @msg_04 @msg_05 @msg_06
- [ ] T029 2026-11-21: The `slop_away-msg` pre-commit hook at the commit-msg stage. Tags: @precommit_04

## Slice 8: Agent hooks and init

- [ ] T030 2026-11-21: The hook test harness and the bash hook scripts for PostToolUse, Stop, and PreToolUse. Tags: @hooks_01 @hooks_02 @hooks_03 @hooks_04 @hooks_05 @hooks_06 @hooks_07
- [ ] T031 2026-11-21: `slop_away init`. Tags: @init_01 @init_02 @init_03 @init_04 @init_05 @init_06 @init_07

## Slice 9: Validation

- [ ] T032 2026-11-21: The corpus test harness and corpus suite, seeded with the slop_away repo's own docs. Tags: @corpus_01 @corpus_02 @corpus_03 @corpus_04 @corpus_05
- [ ] T033 2026-11-21: Property tests P1 to P5. Tags: none
- [ ] T034 2026-11-21: Differential tests X1 and X2. Tags: none
- [ ] T035 2026-11-21: Add the owner's bad docs to the corpus. Auto-fix them into `fixed/` for the owner to clean by hand. Tags: @corpus_01 @corpus_02

## Done

- [x] T001 2026-11-21: Create the Poetry project: Python 3.14, package `slop_away`, console command `slop_away`. Tags: @cli_01
- [x] T002 2026-11-21: Add dev dependencies pytest, pytest-bdd, Hypothesis, and pytest-cov. Confirm pytest-bdd runs on Python 3.14. Tags: none
- [x] T003 2026-11-21: Create `tests/features/`, `tests/properties/`, `tests/differential/`, and the corpus folders `bad/`, `fixed/`, `good/`, with a format for each bad document's expected codes. Tags: none
- [x] T004 2026-11-21: Write the api and cli test harnesses. Tags: none
- [x] T005 2026-11-21: Add `.pre-commit-hooks.yaml` and the CI workflow that runs `pre-commit run --all-files`. Tags: none
- [x] T006 2026-11-21: CLI basics. Tags: @cli_02 @cli_03 @cli_04 @cli_05
- [x] T007 2026-11-21: Config loading, precedence, validation, `select`, and `ignore`. Tags: @config_01 @config_02 @config_03 @config_04 @config_05 @config_06 @config_07 @config_11
- [x] T008 2026-11-21: File selection. Tags: @selection_01 @selection_02 @selection_03 @selection_04 @selection_05 @selection_06
- [x] T009 2026-11-21: Markdown parsing and prose extraction. Tags: @markdown_01 @markdown_02 @markdown_03 @markdown_04 @markdown_05 @markdown_07
- [x] T010 2026-11-21: `text` and `agent` output formats. Tags: @output_01 @output_02 @output_03
- [x] T011 2026-11-21: Rules INJ001 to INJ004. Tags: @inj_01 @inj_02 @inj_03 @inj_04 @inj_05 @inj_06 @inj_07 @inj_08
- [x] T012 2026-11-21: The git test harness and the `slop_away` pre-commit hook. Tags: @precommit_01 @precommit_02
- [x] T013 2026-11-21: VRB rules, and HTML comments skipped by prose rules. Tags: @vrb_01 @vrb_02 @vrb_03 @vrb_04 @vrb_05 @vrb_06 @markdown_06
- [x] T014 2026-11-21: RDB rule. Tags: @rdb_01 @rdb_02 @rdb_03 @rdb_04
- [x] T015 2026-11-21: Profiles. Tags: @config_08
- [x] T016 2026-11-21: Parser interface backed by the spaCy small English model, with the model wheel pinned as a dependency. Tags: none
- [x] T017 2026-11-21: Procedure detection, STE001, and STE002. Tags: @ste_01 @ste_02 @ste_03 @ste_04
- [x] T018 2026-11-21: STE003 to STE006. Tags: @ste_05 @ste_06 @ste_07 @ste_08
- [x] T019 2026-11-21: STE007 and the config glossary. Tags: @ste_09
- [x] T020 2026-11-21: `slop_away sync` and the package cache. Tags: @sync_01 @sync_02 @sync_03
- [x] T021 2026-11-21: Load Vale YAML rules of types existence, substitution, occurrence, and sequence. Tags: @ait_01 @ait_02 @ait_03 @ait_04 @ait_05 @ait_06 @ait_07 @ait_08
- [x] T022 2026-11-21: The `slop_away-sync` pre-commit hook. Tags: @precommit_03
- [x] T023 2026-11-21: Safe fixes with `--fix`. Tags: @fix_01 @fix_04 @fix_05 @fix_06
- [x] T024 2026-11-21: Unsafe fixes with `--unsafe-fixes`. Tags: @fix_02 @fix_03
