Feature: Corpus
  The validation corpus pins down what the rules flag on real documents.

  @corpus_01
  Scenario: Each bad document produces exactly its expected codes
    Given the bad documents in the corpus
    When check_files runs on each document
    Then each document's codes equal its expected codes

  @corpus_02
  Scenario: Each fixed document produces no findings
    Given the fixed documents in the corpus
    When check_files runs on each document
    Then each document has no findings

  @corpus_03
  Scenario: Each good document produces no findings
    Given the good documents in the corpus
    When check_files runs on each document
    Then each document has no findings

  @corpus_04
  Scenario: A change in findings names each affected document
    Given a bad document whose expected codes leave out a code it produces
    When the corpus comparison runs
    Then the comparison report names that document

  @corpus_05
  Scenario: The slop_away repository's own docs produce no findings
    Given the slop_away repository root
    When I run "slop_away check ."
    Then the exit code is 0
