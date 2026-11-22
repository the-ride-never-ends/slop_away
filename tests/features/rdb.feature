Feature: RDB rule
  Each h2 section must stay at or below its Flesch-Kincaid grade limit.

  @rdb_01
  Scenario: RDB001 flags an h2 section above the grade limit
    Given the default config
    When check_text runs on "docs/guide.md" with the text:
      """
      ## Architecture

      The implementation of comprehensive configuration management necessitates considerable organizational coordination across numerous interdependent infrastructure components.
      """
    Then check_text returns a finding with code "RDB001"

  @rdb_02
  Scenario: An h2 section at or below the limit passes
    Given the default config
    When check_text runs on "docs/guide.md" with the text:
      """
      ## Usage

      The tool reads the file. It checks each line. It prints the result.
      """
    Then check_text returns no finding with code "RDB001"

  @rdb_03
  Scenario: A profile changes the grade limit
    Given a file "slop_away.toml" containing:
      """
      [profiles."docs/design/*.md"]
      max-grade = 40
      """
    And the config is loaded from the project root
    When check_text runs on "docs/design/arch.md" with the text:
      """
      ## Architecture

      The implementation of comprehensive configuration management necessitates considerable organizational coordination across numerous interdependent infrastructure components.
      """
    Then check_text returns no finding with code "RDB001"

  @rdb_04
  Scenario: Lists, tables, and code do not count toward the score
    Given the default config
    When check_text runs on "docs/guide.md" with the text:
      """
      ## Components

      - Comprehensive configuration management infrastructure
      - Considerable organizational coordination requirements

      | Component | Responsibility |
      |-----------|----------------|
      | Orchestrator | Interdependent infrastructure synchronization |
      """
    Then check_text returns no finding with code "RDB001"
