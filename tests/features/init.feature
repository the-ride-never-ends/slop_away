Feature: Init
  slop_away init sets up a project in one step.

  @init_01
  Scenario Outline: init writes every part by default
    Given an empty project directory
    When I run "slop_away init"
    Then the file "<path>" exists

    Examples:
      | path                                     |
      | slop_away.toml                           |
      | .pre-commit-config.yaml                  |
      | .github/workflows/slop_away.yml          |
      | .claude/hooks/slop_away_post_edit.sh     |
      | .claude/hooks/slop_away_stop.sh          |
      | .claude/hooks/slop_away_pre_bash.sh      |
      | .claude/settings.json                    |
      | .gitignore                               |

  @init_02
  Scenario Outline: Each skip flag leaves out its part
    Given an empty project directory
    When I run "slop_away init <flag>"
    Then the file "<path>" does not exist

    Examples:
      | flag              | path                                 |
      | --skip-config     | slop_away.toml                       |
      | --skip-pre-commit | .pre-commit-config.yaml              |
      | --skip-ci         | .github/workflows/slop_away.yml      |
      | --skip-hooks      | .claude/hooks/slop_away_stop.sh      |

  @init_03
  Scenario Outline: An existing slop_away.toml stops init before it writes anything
    Given an empty project directory
    And a file "slop_away.toml" containing:
      """
      select = ["INJ"]
      """
    When I run "slop_away init"
    Then <check>

    Examples:
      | check                                             |
      | the exit code is 2                                |
      | stderr contains "slop_away.toml"                  |
      | the file ".pre-commit-config.yaml" does not exist |

  @init_04
  Scenario: init does not write CODEOWNERS
    Given an empty project directory
    When I run "slop_away init"
    Then the file "CODEOWNERS" does not exist

  @init_05
  Scenario Outline: init adds its hooks to an existing pre-commit config
    Given an empty project directory
    And a file ".pre-commit-config.yaml" containing:
      """
      repos:
        - repo: https://github.com/astral-sh/ruff-pre-commit
          rev: v0.14.0
          hooks:
            - id: ruff
      """
    When I run "slop_away init"
    Then <check>

    Examples:
      | check                                                                  |
      | the exit code is 0                                                     |
      | the file ".pre-commit-config.yaml" contains "id: slop_away"            |
      | the file ".pre-commit-config.yaml" contains "astral-sh/ruff-pre-commit" |

  @init_06
  Scenario Outline: init adds its hook entries to an existing Claude Code settings file
    Given an empty project directory
    And a file ".claude/settings.json" containing:
      """
      {"permissions": {"allow": ["Bash(ls)"]}}
      """
    When I run "slop_away init"
    Then <check>

    Examples:
      | check                                                              |
      | the exit code is 0                                                 |
      | the file ".claude/settings.json" contains "slop_away_post_edit.sh" |
      | the file ".claude/settings.json" contains "Bash(ls)"               |

  @init_07
  Scenario Outline: init adds the cache folder to an existing .gitignore
    Given an empty project directory
    And a file ".gitignore" containing:
      """
      dist/
      """
    When I run "slop_away init"
    Then <check>

    Examples:
      | check                                      |
      | the exit code is 0                         |
      | the file ".gitignore" contains ".slop_away/" |
      | the file ".gitignore" contains "dist/"     |
