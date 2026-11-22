Feature: Agent hooks
  The Claude Code hook scripts feed findings back to the agent.

  @hooks_01
  Scenario: The post-edit hook reports findings in an edited Markdown file
    Given a file "docs/a.md" containing:
      """
      You must run the tests first.
      """
    When the post-edit hook script runs with a Write event for "docs/a.md"
    Then the exit code is 2
    And stderr contains "INJ001"

  @hooks_02
  Scenario: The post-edit hook passes a clean file
    Given a file "docs/a.md" containing:
      """
      The tool reads the file.
      """
    When the post-edit hook script runs with a Write event for "docs/a.md"
    Then the exit code is 0

  @hooks_03
  Scenario: The post-edit hook ignores files that are not Markdown
    Given a file "src/app.py" containing:
      """
      # You must run the tests first.
      """
    When the post-edit hook script runs with a Write event for "src/app.py"
    Then the exit code is 0

  @hooks_04
  Scenario: The stop hook blocks while findings remain
    Given a file "docs/a.md" containing:
      """
      You must run the tests first.
      """
    When the stop hook script runs with stop_hook_active false
    Then the exit code is 2

  @hooks_05
  Scenario: The stop hook allows stopping on the second pass
    Given a file "docs/a.md" containing:
      """
      You must run the tests first.
      """
    When the stop hook script runs with stop_hook_active true
    Then the exit code is 0

  @hooks_06
  Scenario Outline: The pre-bash hook blocks commits that skip hooks
    When the pre-bash hook script runs with the command "<command>"
    Then the exit code is 2

    Examples:
      | command                        |
      | git commit --no-verify -m wip  |
      | git commit -n -m wip           |

  @hooks_07
  Scenario: The pre-bash hook allows a normal commit
    When the pre-bash hook script runs with the command "git commit -m wip"
    Then the exit code is 0
