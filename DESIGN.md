# slop_away design

Date: 2026-11-21
Status: approved for Phase 1

This file records the reason behind each design decision. It is for the
owner and for architects. Implementers work from MVP.md, ROADMAP.md,
FEATURE_MAP.md, TODO.md, and the feature files, which carry no rationale.

## Problem

LLM projects produce documentation that is verbose and hard to read. A
prompt that tells the model to write better does not hold, because the
habits come from training data. Docs that a later agent loads as context
can also contain text that the agent reads as instructions.

slop_away checks documentation mechanically and blocks the commit when a
check fails. The agent must revise the text before it can continue.

## Product

| ID  | Decision | Why |
|-----|----------|-----|
| D01 | Private tool, MIT license. Built for the owner's repos first, in a form that can be published later. | Defaults need proof on real repos before other people adopt them. |
| D02 | One CLI in the style of ruff: one command, one config, rule codes, select and ignore. | The owner wants the ruff experience for docs. |
| D03 | The name is `slop_away` for the package, the command, the `[tool.slop_away]` section, and `slop_away.toml`. | One spelling everywhere. |
| D04 | Python 3.14. Poetry for development. | Owner's toolchain. spaCy 3.8.16 ships CPython 3.14 wheels. |
| D05 | Hosted in a private GitHub repo. Installed from git with `uv tool install` or `pipx`. Not on PyPI. | Private tool. Pre-commit fetches hooks with git, so one repo is both the tool and the hook source. |

## Readers and goals

| ID  | Decision | Why |
|-----|----------|-----|
| D06 | Primary readers are developers, including non-native English speakers, and LLMs that load docs as context. | Text that is clear to a non-native reader is also easy for a model to parse. |
| D07 | Goals: less verbosity, better readability, no unintentional prompt injection across agent runs. | Verbose docs waste tokens. Directives in docs get obeyed by the next agent. |

## Architecture

| ID  | Decision | Why |
|-----|----------|-----|
| D08 | Hybrid engine. slop_away runs the prose rules. lychee checks links and rumdl checks Markdown structure. | The prose rules need sentence parsing that Vale's rule types lack. A new link checker adds nothing. |
| D09 | In Phase 1, lychee and rumdl run beside slop_away in pre-commit. One combined report is Phase 3. | Merging other tools' output, versions, and errors is work that is not needed yet. |
| D10 | spaCy small English model behind a parser interface. The model wheel is pinned as a dependency. | Enough for part-of-speech and passive-voice detection. A pinned wheel installs in one step and works offline. The interface allows a swap if the corpus shows accuracy gaps. |
| D11 | slop_away reads Vale YAML rules of four types: existence, substitution, occurrence, and sequence. | These four cover all 134 ai-tells rules: 129 existence, 3 sequence, 1 substitution, 1 occurrence. slop_away's own readability rule replaces Vale's. |
| D12 | External rule packages are fetched by `slop_away sync` into a cache, not bundled. `check` never uses the network. A configured package that is not synced is an error. The cache is `.slop_away/packages/` at the repo root, and `init` adds `.slop_away/` to .gitignore. | ai-tells states no license. Offline checks give the same result every time. A missing rule set must fail loudly, not pass silently. |

## Inputs

| ID  | Decision | Why |
|-----|----------|-----|
| D13 | Phase 1 checks GitHub-flavored Markdown `.md` files and commit messages. | The owner's docs are mostly `.md` files. |
| D14 | Prose rules skip code blocks, inline code, front matter, URLs, and tables. HTML comments are checked by the INJ rules only. Link text counts as prose. | Skipped parts are not prose or distort scores. Hidden comments are an injection channel. Readers see link text. |
| D15 | File selection follows ruff: `include`, `exclude`, `extend-exclude`, recursive globs such as `docs/**/*.md`, and `.gitignore` respected. Profiles apply rule sets per glob. | Familiar model. Profiles let hand-off docs or procedures get their own limits, and let full STE plug in later. |
| D50 | slop_away.toml takes precedence over `[tool.slop_away]` in pyproject.toml. A pyproject.toml without the section is ignored. | Matches ruff, which prefers ruff.toml over pyproject.toml. |

## Rules

| ID  | Decision | Why |
|-----|----------|-----|
| D16 | Ruff rule model: each rule has a code, rules are selected or ignored, and there are no severity levels. Any finding fails the run. | Agents ignore warnings. |
| D17 | All native rule groups are on by default. External packages are off until the config lists them in `packages`. Without an explicit `select`, the default is every native group plus every listed package. An explicit `select` replaces the default. `select` and `ignore` accept package names such as `ai-tells` and rule codes such as `ai-tells.Dash`. | The tool exists to be strict with agents. This reverses ruff's small default set on purpose. |
| D18 | STE001 to STE007 form a subset of ASD-STE100: sentence length, paragraph length, active voice, no contractions, simple tenses, noun clusters of at most 3 nouns, and one term per meaning from a config glossary. Full ASD-STE100 is Phase 5, as an opt-in profile. | Full STE needs the official dictionary and reads stilted outside procedures. |
| D19 | Numbered list steps and sentences that start with an imperative verb count as procedures. Procedures allow 20 words per sentence. Descriptions allow 25. | These are the STE limits. The tool needs a mechanical way to tell the two apart. |
| D20 | RDB scores Flesch-Kincaid per h2 section. The default limit is grade 10, and each profile can change it. | A document score hides bad sections. A paragraph is too short to score reliably. |
| D21 | VRB checks filler and hedge phrases, word budgets per glob, and repeated content. Two sentences count as repeated when they match after normalizing case and whitespace and have at least 8 words. Throat-clearing detection is deferred. | Short sentences such as "Run the tests." repeat for good reasons. Throat-clearing is hard to detect with rules. Add it if the corpus shows it is common. |
| D22 | INJ is four separate rules: INJ001 directives, INJ002 role markers, INJ003 stale action items, INJ004 hidden text. Agent instruction files (AGENTS.md, CLAUDE.md, SKILL.md) get only INJ002 to INJ004. | Directives are the purpose of instruction files. Role markers, stale items, and hidden text are never wanted anywhere. |
| D23 | INJ003 requires each action item to carry a status or a date. | Undated "next step" lines get executed by a later agent after they are stale. |
| D24 | MSG checks commit messages, run with `slop_away check --commit-msg PATH`: subject of at most 72 characters, imperative mood, no trailing period, a body word budget, plus AIT, INJ002 to INJ004, and the VRB filler rules. Trailers are skipped. | An imperative subject is the git convention, so INJ001 does not apply. |
| D25 | External Vale rules keep their own names, such as `ai-tells.Dash`. | The name shows where a rule came from. |

## Fixes

| ID  | Decision | Why |
|-----|----------|-----|
| D26 | `--fix` applies safe fixes. `--unsafe-fixes` also applies fixes that may change meaning. A fix counts as unsafe until the corpus shows it is safe. | The ruff split. A wrong safe fix silently changes what a doc says. |
| D27 | Safe: whitespace, Markdown structure, hidden-text removal, contraction expansion. Unsafe: word swaps and filler deletion. Findings only, with no fix: sentence splits, passive to active, directive removal. | Rewrites need judgment. The agent in the loop does them, so the tool stays deterministic and testable. |

## Suppression and adoption

| ID  | Decision | Why |
|-----|----------|-----|
| D28 | No inline suppression. Exceptions go only in `per-file-ignores` in the config. | Agents use any escape hatch. Config changes show up in review. |
| D29 | CODEOWNERS with required human review covers the config and baseline files. | Works for every agent without detecting which commits came from an agent. |
| D30 | Baseline file `slop_away.baseline.json` at the repo root. A finding's fingerprint is its rule code, its file path, and a hash of the normalized sentence or section text. `check --write-baseline` writes the file. `check` reads it when present. Each finding carries its fingerprint, computed when the check runs. | Old findings do not block adoption. Moving lines does not break a match. Editing a sentence makes its findings new. |

## Output

| ID  | Decision | Why |
|-----|----------|-----|
| D31 | Output formats: text, JSON, agent, and GitHub annotations. SARIF is deferred. The agent format prints one finding per line: code, location, message, and fix hint. | The agent format keeps token cost low. |
| D32 | Findings go to stdout. Exit code 0 means clean, 1 means findings, 2 means a usage or internal error. | Ruff's convention. The owner's hook scripts already map these codes. |

## Integrations

| ID  | Decision | Why |
|-----|----------|-----|
| D33 | Phase 1 ships `.pre-commit-hooks.yaml` with check, sync, and commit-msg hooks, plus Claude Code hooks. Codex hooks are Phase 2. | Owner's order. Codex loads project hooks only when the project's `.codex/` layer is trusted. |
| D34 | slop_away ships its own bash hook scripts, one per hook event, using `jq`. `init` writes them into the project. They are separate from the owner's personal hook scripts. | Keeps slop_away's hooks self-contained and reusable for Codex in Phase 2. Phase 4 needs a Windows replacement for them. |
| D35 | PostToolUse gives feedback after each edit. Stop blocks the agent from finishing while findings remain, for one pass, using `stop_hook_active`. After that, the commit hook blocks. | Fast feedback without trapping the session. Claude Code also ends a turn after 8 consecutive stop-hook blocks. |
| D36 | `init` writes the config, pre-commit entries, the commit-msg hook, the CI workflow, and the Claude Code hook scripts and settings entries by default. Flags skip parts. CODEOWNERS is set up by hand. | Leaving out the agent hooks removes feedback during the session. CODEOWNERS needs a GitHub username and branch protection, which `init` cannot set. |
| D48 | Phase 1 CI is a plain GitHub Actions workflow that runs `pre-commit run --all-files`. The custom GitHub Action is Phase 2. | The git hook alone can be skipped. CI is the floor for every author. |
| D49 | A Claude Code PreToolUse hook blocks `git commit --no-verify`. | Without it, an agent can skip every check with one flag. |
| D51 | `init` adds its entries to an existing `.pre-commit-config.yaml`, `.claude/settings.json`, and `.gitignore`. When any other target file already exists, it exits 2 and writes nothing. There is no `--force`. | Most repos already have those three files. For the rest, fail fast: a partial write is worse than none. YAGNI for `--force`. |

## Platforms

| ID  | Decision | Why |
|-----|----------|-----|
| D37 | Phase 1 runs on WSL or Linux and GitHub Actions. Native Windows is Phase 4. | The owner works in WSL. Windows support costs testing time. |

## Testing

| ID  | Decision | Why |
|-----|----------|-----|
| D38 | Behavior is specified in Gherkin `.feature` files bound to pytest with pytest-bdd. One file per area. Scenario IDs are lowercase tags with an underscore, such as `@inj_03`, which FEATURE_MAP.md and TODO.md reference. Unit scenarios test the public Python API through return values and raised exceptions. End-to-end scenarios test the CLI, hooks, and git through exit codes and output. Each Then step checks one thing. | The specs run as tests. Unit scenarios run fast and fail precisely. End-to-end scenarios cover the integration. pytest-bdd turns tags into pytest markers, so tags must be valid marker names. The lowercase form cannot be confused with rule codes such as INJ003. |
| D39 | A validation corpus holds bad, fixed, and good documents. Bad documents must produce exactly their expected codes. Fixed and good documents must produce none. | Exact codes also catch new false positives on bad documents. |
| D40 | Fixed documents are made by auto-fixing bad ones and then cleaning them by hand. The hand cleanup is judged by a cold read, not by the rules. | Fixes judged only by the linter prove only that the linter agrees with itself. Good documents guard against over-flagging. |
| D41 | slop_away lints its own docs and commit messages. They also seed the corpus. | Free test data. A linter whose own docs fail its rules is hard to trust. |
| D42 | Property tests with Hypothesis: safe fixes are idempotent; baseline fingerprints survive line moves; code-block content never changes findings; the parser never crashes and either succeeds or exits 2; findings do not depend on file order. | These properties hold for all inputs, which example tests cannot cover. |
| D43 | Differential tests: readability scores against textstat or Vale with a tolerance of 0.5 grade; Vale-compatible rules against Vale on the corpus. Version-to-version differential tests are Phase 2. | Both comparisons have an outside reference. Syllable counting differs between tools, so scores need a tolerance. |
| D44 | Benchmarking is Phase 2, with pytest-benchmark. Target: under 2 seconds to check one typical Markdown file. | The hooks run on every edit. |
| D45 | Test stack: pytest, pytest-bdd, Hypothesis, pytest-cov. Other plugins join in the phase that first uses them. | YAGNI. |

## Documents

| ID  | Decision | Why |
|-----|----------|-----|
| D46 | The document set is DESIGN.md, MVP.md, ROADMAP.md, FEATURE_MAP.md, TODO.md, and the feature files. Each fact lives in one place. Other files refer to scenario tags instead of restating behavior. | DRY. The feature files own behavior. |
| D47 | TODO.md items carry a checkbox, an ID, a date, and scenario tags. A status appears only for doing and blocked. Done items move to a Done section. The agent may add items and change their status. Only the owner deletes items or changes scope. These editing rules live in the owner's AGENTS file. | Instructions belong in instruction files. The format passes INJ003. |

## Phases

1. MVP, split into sections that each work end to end.
2. Codex hooks, GitHub Action, PR descriptions, benchmarking, version-to-version differential tests.
3. Docstrings, code comments, one combined report.
4. Native Windows.
5. Full ASD-STE100.

## Open items

- pytest-bdd 8.1.0 lists Python 3.9 to 3.13 in its classifiers. Fedora builds it for Python 3.14. Confirm it in the first CI run.
