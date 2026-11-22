Feature: Pre-commit hooks
  The hooks in .pre-commit-hooks.yaml block commits that fail the checks.

  Background:
    Given a git repository with the slop_away pre-commit hooks installed

  @precommit_01
  Scenario: The slop_away hook blocks a commit with findings
    Given a staged file "docs/a.md" containing:
      """
      You must run the tests first.
      """
    When I run "git commit -m 'Add the guide'"
    Then the exit code is not 0

  @precommit_02
  Scenario: The slop_away hook allows a clean commit
    Given a staged file "docs/a.md" containing:
      """
      The tool reads the file.
      """
    When I run "git commit -m 'Add the guide'"
    Then the exit code is 0

  @precommit_03
  Scenario: The slop_away-sync hook syncs configured packages
    Given a local server that serves the package "test-pkg"
    And a file "slop_away.toml" that lists the package "test-pkg" from the local server
    When I run "pre-commit run slop_away-sync --all-files"
    Then the package cache contains "test-pkg"

  @precommit_04
  Scenario: The slop_away-msg hook blocks a commit message with findings
    Given a staged file "docs/a.md" containing:
      """
      The tool reads the file.
      """
    When I run "git commit -m 'Added the guide.'"
    Then the exit code is not 0
