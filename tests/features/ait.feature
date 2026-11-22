Feature: Vale-compatible rules
  slop_away reads Vale YAML rules from synced packages.

  @ait_01
  Scenario: An existence rule flags its token at its position
    Given a synced package "test-pkg" with the rule file "Delve.yml":
      """
      extends: existence
      message: "Avoid '%s'."
      tokens:
        - delve
      """
    And a config that lists the package "test-pkg"
    When check_text runs on "docs/guide.md" with the text "We delve into the parser."
    Then check_text returns a finding with code "test-pkg.Delve"
    And that finding has column 4

  @ait_02
  Scenario: A substitution rule names the replacement
    Given a synced package "test-pkg" with the rule file "Use.yml":
      """
      extends: substitution
      message: "Use '%s' instead of '%s'."
      swap:
        utilize: use
      """
    And a config that lists the package "test-pkg"
    When check_text runs on "docs/guide.md" with the text "We utilize the parser."
    Then check_text returns a finding with code "test-pkg.Use"
    And that finding's message contains "'use'"

  @ait_03
  Scenario: An occurrence rule flags a count over its limit
    Given a synced package "test-pkg" with the rule file "Very.yml":
      """
      extends: occurrence
      message: "Too many uses of 'very'."
      scope: sentence
      max: 1
      token: very
      """
    And a config that lists the package "test-pkg"
    When check_text runs on "docs/guide.md" with the text "It is very very fast."
    Then check_text returns a finding with code "test-pkg.Very"

  @ait_04
  Scenario: A sequence rule flags its part-of-speech pattern
    Given a synced package "test-pkg" with the rule file "Seamless.yml":
      """
      extends: sequence
      message: "Avoid 'seamless' before a noun."
      tokens:
        - pattern: seamless
        - tag: NN
      """
    And a config that lists the package "test-pkg"
    When check_text runs on "docs/guide.md" with the text "It gives a seamless experience."
    Then check_text returns a finding with code "test-pkg.Seamless"

  @ait_05
  Scenario: External findings use the package's rule name
    Given a synced package "test-pkg" with the rule file "Delve.yml":
      """
      extends: existence
      message: "Avoid '%s'."
      tokens:
        - delve
      """
    And a config that lists the package "test-pkg"
    When check_text runs on "docs/guide.md" with the text "We delve into the parser."
    Then every finding from the package has a code starting with "test-pkg."

  @ait_06
  Scenario: A synced package that the config does not list does not run
    Given a synced package "test-pkg" with the rule file "Delve.yml":
      """
      extends: existence
      message: "Avoid '%s'."
      tokens:
        - delve
      """
    And the default config
    When check_text runs on "docs/guide.md" with the text "We delve into the parser."
    Then check_text returns no finding with code "test-pkg.Delve"
