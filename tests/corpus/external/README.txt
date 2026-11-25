External corpus

This group contains 30 English Markdown documents from public GitHub
repositories. The corpus uses source snapshots from two date ranges:
through 2021, and from 2023. The source commit sets the date range.

The draw uses seed 20261123. The script increments the seed after each
attempt. It samples without replacement within each type and date group.
The source list records every draw, including rejected candidates.

The candidate list is fixed in candidates.json. Its search queries and
source commits are recorded there. The first three queries use the first
30 MIT results and the first 15 results for each other license. The two
added queries use their first 30 results to supply older design and
roadmap documents. A truncated source tree does not enter the list.
The candidate types follow file names and directory names. No linter
result controls the draw.

A document needs at least 150 words of visible prose. Code, tables, and
bare links cannot occupy more than half its lines. Its source repository
needs at least 20 stars and an MIT, Apache-2.0, or BSD license at the pinned
commit. The licenses directory contains the source license notices.
licenses.json also records the source license files for candidate commits.

The owner restricted the project to English after the first draw. The
current draw uses the same seed with that scope rule. The language check
uses langdetect 1.0.9 with seed zero. It checks visible prose after space
normalization. English must have a probability of at least 0.95. The check
rejects text with no language features. The initial draw is superseded.
The selected Markdown files all pass the English check.

The tests check source hashes, language, size, and each type and date quota.
Downloaded source documents keep their original text. Source notices also
keep their original text. The prose rules can report findings in them.

Run the draw from the repository root with network access:

    poetry run python -m tests.generation.draw --seed 20261123

The script finishes its draw before it writes the selected source files.
It fails on download errors. Temporary HTTP 503 errors get three attempts.
