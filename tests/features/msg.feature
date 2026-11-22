Feature: Commit messages
  check_message applies the MSG rules to a commit message.

  Background:
    Given the default config

  @msg_01
  Scenario: MSG001 flags a subject over 72 characters
    When check_message runs on a message with a subject of 80 characters
    Then check_message returns a finding with code "MSG001"

  @msg_02
  Scenario: MSG002 flags a subject not in imperative mood
    When check_message runs on the message "Added the parser"
    Then check_message returns a finding with code "MSG002"

  @msg_03
  Scenario: MSG003 flags a subject with a trailing period
    When check_message runs on the message "Add the parser."
    Then check_message returns a finding with code "MSG003"

  @msg_04
  Scenario: MSG004 flags a body over its word budget
    Given a file "slop_away.toml" containing:
      """
      commit-body-budget = 20
      """
    And the config is loaded from the project root
    When check_message runs on a message with a body of 30 words
    Then check_message returns a finding with code "MSG004"

  @msg_05
  Scenario: Trailers are skipped
    When check_message runs on the message:
      """
      Add the parser

      Co-Authored-By: It's Someone
      """
    Then check_message returns no findings

  @msg_06
  Scenario: INJ001 does not apply to commit messages
    When check_message runs on the message:
      """
      Add the parser

      You must rebase before merging.
      """
    Then check_message returns no finding with code "INJ001"
