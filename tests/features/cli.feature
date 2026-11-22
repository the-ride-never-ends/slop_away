Feature: CLI basics
  The slop_away command reports findings through its exit code and output.

  @cli_01
  Scenario: --version prints the version
    When I run "slop_away --version"
    Then the exit code is 0
    And stdout matches "^\d+\.\d+\.\d+$"

  @cli_02
  Scenario: A clean file exits 0 with no output
    Given a file "docs/a.md" containing:
      """
      # Setup

      The tool reads the file. It checks each line.
      """
    When I run "slop_away check docs/a.md"
    Then the exit code is 0
    And stdout is empty

  @cli_03
  Scenario: A file with findings exits 1
    Given a file "docs/a.md" containing:
      """
      # Setup

      You must run the tests first.
      """
    When I run "slop_away check docs/a.md"
    Then the exit code is 1

  @cli_04
  Scenario: An unknown option exits 2
    When I run "slop_away check --bogus"
    Then the exit code is 2

  @cli_05
  Scenario: A path that does not exist exits 2 and names the path
    When I run "slop_away check docs/missing.md"
    Then the exit code is 2
    And stderr contains "docs/missing.md"
