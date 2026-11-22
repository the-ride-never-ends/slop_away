Feature: Markdown extraction
  Prose rules check only the prose a reader sees.

  Background:
    Given the default config

  @markdown_01
  Scenario: Text in a fenced code block produces no findings
    When check_text runs on "docs/guide.md" with the text:
      """
      ```text
      You must run the tests first. It's worth noting that this is fine.
      ```
      """
    Then check_text returns no findings

  @markdown_02
  Scenario: Inline code produces no findings
    When check_text runs on "docs/guide.md" with the text:
      """
      The flag is `--don't-ask`.
      """
    Then check_text returns no findings

  @markdown_03
  Scenario: Front matter produces no findings
    When check_text runs on "docs/guide.md" with the text:
      """
      ---
      description: You must read this. It's important.
      ---

      The tool reads the file.
      """
    Then check_text returns no findings

  @markdown_04
  Scenario: A bare URL produces no findings
    When check_text runs on "docs/guide.md" with the text:
      """
      The source is at https://example.com/dont-do-this/its-fine.
      """
    Then check_text returns no findings

  @markdown_05
  Scenario: Table cells produce no prose findings
    When check_text runs on "docs/guide.md" with the text:
      """
      | Option | Meaning |
      |--------|---------|
      | quiet  | Don't print progress |
      """
    Then check_text returns no finding with code "STE004"

  @markdown_06
  Scenario: An HTML comment is skipped by prose rules
    When check_text runs on "docs/guide.md" with the text:
      """
      <!-- The parser doesn't stop here. -->
      The tool reads the file.
      """
    Then check_text returns no finding with code "STE004"

  @markdown_07
  Scenario: Link text is checked as prose
    When check_text runs on "docs/guide.md" with the text:
      """
      Read [what you shouldn't do](https://example.com/rules).
      """
    Then check_text returns a finding with code "STE004"
