Feature: Baseline
  Findings recorded in the baseline do not fail the run.

  @baseline_01
  Scenario: check --write-baseline writes the baseline file
    Given a file "docs/a.md" containing:
      """
      The tool doesn't run twice.
      """
    When I run "slop_away check docs/a.md --write-baseline"
    Then the file "slop_away.baseline.json" exists

  @baseline_02
  Scenario: Findings in the baseline do not fail the run
    Given a file "docs/a.md" containing:
      """
      The tool doesn't run twice.
      """
    And I have run "slop_away check docs/a.md --write-baseline"
    When I run "slop_away check docs/a.md"
    Then the exit code is 0

  @baseline_03
  Scenario: A finding not in the baseline fails the run
    Given a file "docs/a.md" containing:
      """
      The tool doesn't run twice.
      """
    And I have run "slop_away check docs/a.md --write-baseline"
    And the line "The parser can't stop." is appended to "docs/a.md"
    When I run "slop_away check docs/a.md"
    Then the exit code is 1

  @baseline_04
  Scenario: A baselined finding still matches after its lines move
    Given the default config
    And a baseline built from the findings of check_text on "docs/a.md" with the text "The tool doesn't run twice."
    When check_text runs on "docs/a.md" with the text:
      """
      # Title

      Intro line.

      The tool doesn't run twice.
      """
    Then baseline.matches returns True for the finding with code "STE004"

  @baseline_05
  Scenario: Editing a baselined sentence makes its findings new
    Given the default config
    And a baseline built from the findings of check_text on "docs/a.md" with the text "The tool doesn't run twice."
    When check_text runs on "docs/a.md" with the text "The tool doesn't run three times."
    Then baseline.matches returns False for the finding with code "STE004"

  @baseline_06
  Scenario: A baselined finding still matches after its list marker changes
    Given the default config
    And a baseline built from the findings of check_text on "docs/a.md" with the text "- Never edit generated files."
    When check_text runs on "docs/a.md" with the text "* Never edit generated files."
    Then baseline.matches returns True for the finding with code "INJ001"
