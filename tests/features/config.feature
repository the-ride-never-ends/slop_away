Feature: Config
  load_config reads settings from slop_away.toml or pyproject.toml.

  @config_01
  Scenario: Settings are read from the tool.slop_away section of pyproject.toml
    Given a file "pyproject.toml" containing:
      """
      [tool.slop_away]
      select = ["INJ"]
      """
    When load_config runs on the project root
    Then config.select equals ["INJ"]

  @config_02
  Scenario: Settings are read from slop_away.toml
    Given a file "slop_away.toml" containing:
      """
      select = ["VRB"]
      """
    When load_config runs on the project root
    Then config.select equals ["VRB"]

  @config_03
  Scenario: slop_away.toml takes precedence over pyproject.toml
    Given a file "pyproject.toml" containing:
      """
      [tool.slop_away]
      select = ["INJ"]
      """
    And a file "slop_away.toml" containing:
      """
      select = ["VRB"]
      """
    When load_config runs on the project root
    Then config.select equals ["VRB"]

  @config_04
  Scenario: An unknown key raises ConfigError
    Given a file "slop_away.toml" containing:
      """
      colour = "red"
      """
    When load_config runs on the project root
    Then load_config raises ConfigError
    And the error message contains "colour"

  @config_05
  Scenario: An invalid value raises ConfigError
    Given a file "slop_away.toml" containing:
      """
      select = 5
      """
    When load_config runs on the project root
    Then load_config raises ConfigError
    And the error message contains "select"

  @config_06
  Scenario: select limits the run to the listed rules
    Given a file "slop_away.toml" containing:
      """
      select = ["INJ"]
      """
    And the config is loaded from the project root
    When check_text runs on "docs/guide.md" with the text:
      """
      It is worth noting that the cache is cleared.
      """
    Then check_text returns no finding with code "VRB001"

  @config_07
  Scenario: ignore removes the listed rules
    Given a file "slop_away.toml" containing:
      """
      ignore = ["VRB001"]
      """
    And the config is loaded from the project root
    When check_text runs on "docs/guide.md" with the text:
      """
      It is worth noting that the cache is cleared.
      """
    Then check_text returns no finding with code "VRB001"

  @config_08
  Scenario: A profile changes rule settings for files matching its glob
    Given a file "slop_away.toml" containing:
      """
      [profiles."handoff/**/*.md"]
      ignore = ["VRB001"]
      """
    And the config is loaded from the project root
    When check_text runs on "handoff/notes.md" with the text:
      """
      It is worth noting that the cache is cleared.
      """
    Then check_text returns no finding with code "VRB001"

  @config_09
  Scenario: per-file-ignores removes rules for matching files
    Given a file "slop_away.toml" containing:
      """
      [per-file-ignores]
      "docs/legacy/*.md" = ["VRB001"]
      """
    And the config is loaded from the project root
    When check_text runs on "docs/legacy/old.md" with the text:
      """
      It is worth noting that the cache is cleared.
      """
    Then check_text returns no finding with code "VRB001"

  @config_10
  Scenario: An inline suppression comment has no effect
    Given the default config
    When check_text runs on "docs/guide.md" with the text:
      """
      <!-- slop_away: ignore VRB001 -->
      It is worth noting that the cache is cleared.
      """
    Then check_text returns a finding with code "VRB001"

  @config_11
  Scenario: A pyproject.toml without a tool.slop_away section is ignored
    Given a file "pyproject.toml" containing:
      """
      [tool.poetry]
      name = "example"
      """
    When load_config runs on the project root
    Then the loaded config equals the default config
