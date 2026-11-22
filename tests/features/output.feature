Feature: Output formats
  slop_away check prints findings to stdout in the selected format.

  Background:
    Given a file "docs/a.md" containing:
      """
      # Setup

      The tool doesn't run twice.
      """

  @output_01
  Scenario: The text format shows path, line, column, code, and message
    When I run "slop_away check docs/a.md --output-format text"
    Then stdout matches "^docs/a\.md:3:\d+: STE004 .+$"

  @output_02
  Scenario: The agent format prints one line per finding with a fix hint
    When I run "slop_away check docs/a.md --output-format agent"
    Then stdout matches "^STE004 docs/a\.md:3:\d+ .+ Fix: .+$"

  @output_03
  Scenario: Nothing but findings is printed
    When I run "slop_away check docs/a.md --output-format agent"
    Then stderr is empty

  @output_04
  Scenario: The json format prints a JSON array of findings
    When I run "slop_away check docs/a.md --output-format json"
    Then stdout parses as a JSON array
    And the first element has "code" equal to "STE004"

  @output_05
  Scenario: The github format prints GitHub Actions annotations
    When I run "slop_away check docs/a.md --output-format github"
    Then stdout starts with "::error file=docs/a.md,line=3"
