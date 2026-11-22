Feature: VRB rules
  Docs must not spend words that carry no information.

  @vrb_01
  Scenario Outline: VRB001 flags a filler phrase
    Given the default config
    When check_text runs on "docs/guide.md" with the text "<text>"
    Then check_text returns a finding with code "VRB001"

    Examples:
      | text                                            |
      | It is worth noting that the cache is cleared.   |
      | In order to run the tool, open a shell.         |
      | It is important to note that the tool is fast.  |

  @vrb_02
  Scenario Outline: VRB002 flags a hedge phrase
    Given the default config
    When check_text runs on "docs/guide.md" with the text "<text>"
    Then check_text returns a finding with code "VRB002"

    Examples:
      | text                                |
      | The cache might possibly be stale.  |
      | It seems that the parser is slow.   |
      | This is arguably the best option.   |

  @vrb_03
  Scenario: VRB003 flags a file over its glob's word budget
    Given a file "slop_away.toml" containing:
      """
      [profiles."handoff/**/*.md"]
      word-budget = 50
      """
    And the config is loaded from the project root
    When check_text runs on "handoff/notes.md" with a text of 60 words
    Then check_text returns a finding with code "VRB003"

  @vrb_04
  Scenario: VRB004 flags a sentence repeated within one document
    Given the default config
    When check_text runs on "docs/guide.md" with the text:
      """
      ## Install

      The cache is cleared every time the tool starts a new run.

      ## Run

      The cache is cleared every time the tool starts a new run.
      """
    Then check_text returns a finding with code "VRB004"

  @vrb_05
  Scenario: VRB005 flags a sentence repeated across documents
    Given the default config
    And a file "docs/a.md" containing:
      """
      The cache is cleared every time the tool starts a new run.
      """
    And a file "docs/b.md" containing:
      """
      The cache is cleared every time the tool starts a new run.
      """
    When check_files runs on ["docs/a.md", "docs/b.md"]
    Then check_files returns a finding with code "VRB005"

  @vrb_06
  Scenario: A repeated sentence under 8 words passes
    Given the default config
    When check_text runs on "docs/guide.md" with the text:
      """
      ## Install

      Run the tests.

      ## Release

      Run the tests.
      """
    Then check_text returns no finding with code "VRB004"
