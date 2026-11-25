Accuracy checks

A1 uses labeled template sentences. A2 uses the English external corpus
and the independent Stanza parser. Neither set uses human labels.

The templates cover seven checks. Each check has positive and negative
cases. The first A1 run has 32 cases for each check. Each case holds its
expected label before either parser runs.

A2 uses sentence units from visible source blocks. Stanza supplies word
classes and dependency relations. The reference labels passive voice,
complex tenses, long noun groups, commands, and reader directives.
The command label also supplies the expected MSG002 result.

A command such as "Run the tests." is a procedure step, not a reader
directive. A reader directive has a form from the INJ001 scenarios.
One form is "you" with must, should, shall, need to, or have to.
Another is a command that starts with always, never, or do not. The
last is an IMPORTANT label.

The message comparison checks each source sentence as a message subject.
The hidden-directive comparison checks it inside an HTML comment.
The procedure comparison uses sentences of 21 to 25 words. A procedure
can exceed the 20-word limit, while the same description can pass.
Numbered list steps retain their procedure status.

These labels measure agreement with an independent parser. They do not
prove that either parser is correct. The report records counts for true
and false positives and negatives, and each precision and recall rate.

The optional accuracy dependency group includes Stanza 1.15.1 and
PyTorch 2.9.1 for CPU use. The models use English EWT without character
language models. models.json pins each model hash and the resource
version. Setup downloads models into the virtual environment. The
comparison verifies the hashes and does not download files.

Run these commands from the repository root:

    poetry install --with accuracy
    poetry run python -m tests.accuracy.setup_models
    poetry run python -m tests.accuracy.run --suite templates --output templates-report.json
    poetry run python -m tests.accuracy.run --suite external --output external-report.json

Add --verify to check the owner limits and the recorded rates. The
verification fails when an owner limit is absent. The owner sets each
minimum after the first measured run. The ratchet records that first
run and blocks a later drop. A higher measured rate can pass.

The separate accuracy CI job runs on pull requests to main and once
a week. It saves both reports as artifacts, including failed runs.
