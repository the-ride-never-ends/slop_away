Feature: STE rules
  A subset of the ASD-STE100 writing rules.

  Background:
    Given the default config

  @ste_01
  Scenario: STE001 flags a procedure sentence over 20 words
    When check_text runs on "docs/guide.md" with the text:
      """
      1. Open the configuration file in the root folder of the repository and then change the value of the timeout setting to thirty seconds.
      """
    Then check_text returns a finding with code "STE001"

  @ste_02
  Scenario: STE001 passes a description sentence of 21 to 25 words
    When check_text runs on "docs/guide.md" with the text:
      """
      The configuration file in the root folder of the repository holds the timeout value, the retry count, and the list of excluded paths.
      """
    Then check_text returns no finding with code "STE001"

  @ste_03
  Scenario: STE001 flags a description sentence over 25 words
    When check_text runs on "docs/guide.md" with the text:
      """
      The configuration file in the root folder of the repository holds the timeout value, the retry count, the list of excluded paths, and the name of the default output format.
      """
    Then check_text returns a finding with code "STE001"

  @ste_04
  Scenario: STE002 flags a paragraph over 6 sentences
    When check_text runs on "docs/guide.md" with the text:
      """
      The tool reads files. It finds prose. It checks rules. It collects findings. It sorts them. It prints them. It exits.
      """
    Then check_text returns a finding with code "STE002"

  @ste_05
  Scenario: STE003 flags a passive sentence
    When check_text runs on "docs/guide.md" with the text "The file is read by the parser."
    Then check_text returns a finding with code "STE003"

  @ste_06
  Scenario Outline: STE004 flags a contraction
    When check_text runs on "docs/guide.md" with the text "<text>"
    Then check_text returns a finding with code "STE004"

    Examples:
      | text                       |
      | The tool doesn't run twice. |
      | It's a short file.         |
      | The parser can't stop.     |
      | The cache won't clear.     |

  @ste_07
  Scenario Outline: STE005 flags a sentence not in a simple tense
    When check_text runs on "docs/guide.md" with the text "<text>"
    Then check_text returns a finding with code "STE005"

    Examples:
      | text                             |
      | The parser is reading the file.  |
      | The parser has read the file.    |
      | The parser will have read the file. |

  @ste_08
  Scenario: STE006 flags a noun cluster over 3 nouns
    When check_text runs on "docs/guide.md" with the text "The configuration file parser error message appears."
    Then check_text returns a finding with code "STE006"

  @ste_09
  Scenario: STE007 flags a banned synonym from the glossary
    Given a file "slop_away.toml" containing:
      """
      [glossary]
      directory = ["folder"]
      """
    And the config is loaded from the project root
    When check_text runs on "docs/guide.md" with the text "Open the folder."
    Then check_text returns a finding with code "STE007"
