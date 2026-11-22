Feature: Fixes
  Safe fixes never change meaning. Unsafe fixes run only when asked.

  Background:
    Given the default config

  @fix_01
  Scenario Outline: apply_fixes applies safe fixes
    When apply_fixes runs on "docs/guide.md" with the text "<before>" and unsafe False
    Then apply_fixes returns "<after>"

    Examples:
      | before                      | after                        |
      | The tool doesn't run twice. | The tool does not run twice. |
      | The tool runs.   Then stops. | The tool runs. Then stops.   |

  @fix_02
  Scenario: apply_fixes does not apply unsafe fixes by default
    When apply_fixes runs on "docs/guide.md" with the text "In order to run the tool, open a shell." and unsafe False
    Then apply_fixes returns "In order to run the tool, open a shell."

  @fix_03
  Scenario: apply_fixes applies unsafe fixes when asked
    When apply_fixes runs on "docs/guide.md" with the text "In order to run the tool, open a shell." and unsafe True
    Then apply_fixes returns "To run the tool, open a shell."

  @fix_04
  Scenario: Findings with no fix remain after fixing
    When apply_fixes runs on "docs/guide.md" with the text "The file is read by the parser." and unsafe True
    And check_text runs on "docs/guide.md" with the fixed text
    Then check_text returns a finding with code "STE003"

  @fix_05
  Scenario: A second fix pass changes nothing
    When apply_fixes runs on "docs/guide.md" with the text "The tool doesn't run twice." and unsafe False
    And apply_fixes runs again on its own result
    Then the second result equals the first result

  @fix_06
  Scenario: check --fix rewrites the file on disk
    Given a file "docs/a.md" containing:
      """
      The tool doesn't run twice.
      """
    When I run "slop_away check docs/a.md --fix"
    Then the file "docs/a.md" contains "The tool does not run twice."
