Feature: Package sync
  slop_away sync downloads external rule packages. check never uses the network.

  Background:
    Given a local server that serves the package "test-pkg"
    And a file "slop_away.toml" that lists the package "test-pkg" from the local server
    And a file "docs/a.md" containing:
      """
      We delve into the parser.
      """

  @sync_01
  Scenario: sync downloads configured packages into the cache
    When I run "slop_away sync"
    Then the exit code is 0
    And the package cache contains "test-pkg"

  @sync_02
  Scenario: check exits 2 and names a configured package that is not synced
    When I run "slop_away check docs/a.md"
    Then the exit code is 2
    And stderr contains "test-pkg"

  @sync_03
  Scenario: check runs without network access after sync
    Given I have run "slop_away sync"
    And the local server is stopped
    When I run "slop_away check docs/a.md"
    Then the exit code is 1
    And stdout contains "test-pkg.Delve"
