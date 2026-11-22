Feature: File selection
  select_files picks the Markdown files to check.

  Background:
    Given these files exist:
      | path              |
      | docs/a.md         |
      | docs/sub/b.md     |
      | drafts/c.md       |
      | .venv/d.md        |
      | notes.txt         |

  @selection_01
  Scenario: A recursive glob selects nested files
    Given a file "slop_away.toml" containing:
      """
      include = ["docs/**/*.md"]
      """
    And the config is loaded from the project root
    When select_files runs on ["."]
    Then the result contains "docs/sub/b.md"

  @selection_02
  Scenario: A directory path selects the Markdown files under it
    Given the default config
    When select_files runs on ["docs"]
    Then the result contains "docs/sub/b.md"

  @selection_03
  Scenario: exclude removes matching files
    Given a file "slop_away.toml" containing:
      """
      exclude = ["docs/sub"]
      """
    And the config is loaded from the project root
    When select_files runs on ["."]
    Then the result does not contain "docs/sub/b.md"

  @selection_04
  Scenario Outline: extend-exclude adds to the default excludes
    Given a file "slop_away.toml" containing:
      """
      extend-exclude = ["drafts"]
      """
    And the config is loaded from the project root
    When select_files runs on ["."]
    Then the result does not contain "<path>"

    Examples:
      | path        |
      | drafts/c.md |
      | .venv/d.md  |

  @selection_05
  Scenario: Files listed in .gitignore are skipped
    Given a file ".gitignore" containing:
      """
      drafts/
      """
    And the default config
    When select_files runs on ["."]
    Then the result does not contain "drafts/c.md"

  @selection_06
  Scenario: Files that are not Markdown are skipped
    Given the default config
    When select_files runs on ["."]
    Then the result does not contain "notes.txt"
