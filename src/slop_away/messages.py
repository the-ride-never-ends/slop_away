"""Check commit-message subjects and prose."""

import re
from dataclasses import replace
from pathlib import Path

from slop_away.config import Config
from slop_away.external import scan_external
from slop_away.findings import Finding, make_finding
from slop_away.injection import scan_injection
from slop_away.markdown import Projection, parse_document
from slop_away.packages import load_rules
from slop_away.parsing import PARSER, is_imperative
from slop_away.text import word_matches
from slop_away.verbosity import scan_verbosity

SCISSORS = "# ------------------------ >8 ------------------------"
TRAILER = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*[ \t]*:")
PROSE_CODES = ("INJ002", "INJ003", "INJ004", "VRB001")


def _mask(characters: list[str], start: int, end: int) -> None:
    """Exclude a source range.

    Args:
        characters: The source characters.
        start: The first source offset.
        end: The offset after the range.
    """
    for index in range(start, end):
        if characters[index] not in "\r\n":
            characters[index] = " "


def _parts(text: str) -> tuple[Projection, str, str]:
    """Get the subject and visible message text.

    Args:
        text: The commit-message source.

    Returns:
        The subject, visible message, and visible body.

    Raises:
        ValueError: The message has no subject.
    """
    lines = [
        match
        for match in re.finditer(r"[^\r\n]*(?:\r\n|\r|\n|$)", text)
        if match.start() != match.end()
    ]
    characters = list(text)
    for line in lines:
        if line[0].rstrip("\r\n") == SCISSORS:
            _mask(characters, line.start(), len(text))
            break
        if line[0].startswith("#"):
            _mask(characters, line.start(), line.end())
    visible = "".join(characters)
    content = [visible[line.start() : line.end()] for line in lines]
    subject_index = next(
        (index for index, line in enumerate(content) if line.strip()), None
    )
    if subject_index is None:
        raise ValueError("Commit message needs a nonempty subject.")
    line = lines[subject_index]
    value = content[subject_index]
    start = line.start() + len(value) - len(value.lstrip())
    end = line.start() + len(value.rstrip())
    subject = Projection(text[start:end], tuple(range(start, end)))
    last = len(content)
    while last > subject_index + 1 and not content[last - 1].strip():
        last -= 1
    first = last
    while first > subject_index + 1 and content[first - 1].strip():
        first -= 1
    found = False
    valid = first > subject_index + 1
    for value in content[first:last]:
        if TRAILER.match(value):
            found = True
        elif not (found and value.startswith((" ", "\t"))):
            valid = False
    if valid and found:
        _mask(characters, lines[first].start(), lines[last - 1].end())
    visible = "".join(characters)
    _mask(characters, 0, line.end())
    return subject, visible, "".join(characters)


def check_message(
    text: str, config: Config, path: str | Path = ".git/COMMIT_EDITMSG"
) -> list[Finding]:
    """Check a commit message.

    Args:
        text: The UTF-8 message text.
        config: The project settings.
        path: The logical message path for reports and file settings.

    Returns:
        Findings in source order.

    Raises:
        TypeError: The message is not text.
        ValueError: The message, path, or configured package is invalid.
    """
    if not isinstance(text, str):
        raise TypeError("Expected commit-message text.")
    source = Path(path)
    if source.is_absolute():
        source = source.relative_to(config.root)
    settings = config.for_path(source)
    rules = load_rules(config)
    subject, visible, body = _parts(text)
    findings = []
    problems = []
    if settings.enabled("MSG001") and len(subject.text) > 72:
        problems.append(
            (
                "MSG001",
                subject.offsets[72],
                subject.text,
                (
                    f"Subject has {len(subject.text)} characters; "
                    "the limit is 72."
                ),
                "Use a shorter subject.",
            )
        )
    if settings.enabled("MSG002"):
        initial_words = word_matches(subject.text)
        analysis = subject
        if initial_words:
            first = initial_words[0]
            initial = "".join(
                char.lower() if "A" <= char <= "Z" else char
                for char in first[0]
            )
            analysis = Projection(
                subject.text[: first.start()]
                + initial
                + subject.text[first.end() :],
                subject.offsets,
            )
        sentences = PARSER.parse(analysis)
        if not sentences or not is_imperative(sentences[0]):
            problems.append(
                (
                    "MSG002",
                    subject.offsets[0],
                    subject.text,
                    "Subject is not in imperative mood.",
                    "Start with an imperative verb.",
                )
            )
    if settings.enabled("MSG003") and subject.text.endswith("."):
        problems.append(
            (
                "MSG003",
                subject.offsets[-1],
                subject.text,
                "Subject has a trailing period.",
                "Remove the final period.",
            )
        )
    document = parse_document(visible)
    if settings.enabled("MSG004"):
        body_document = parse_document(body)
        words = [
            (block.prose, word)
            for block in body_document.blocks
            for word in word_matches(block.prose.text)
        ]
        budget = settings.commit_body_budget
        if len(words) > budget:
            prose, word = words[budget]
            context = "\n".join(
                block.prose.text for block in body_document.blocks
            )
            problems.append(
                (
                    "MSG004",
                    prose.offsets[word.start()],
                    context,
                    f"Body has {len(words)} words; the limit is {budget}.",
                    "Remove words from the message body.",
                )
            )
    for code, offset, context, message, hint in problems:
        findings.append(
            make_finding(code, offset, text, source, context, message, hint)
        )
    native = replace(
        settings,
        select=[code for code in PROSE_CODES if settings.enabled(code)],
    )
    findings.extend(scan_injection(text, source, native, document))
    findings.extend(scan_verbosity(text, source, native, document, {}))
    findings.extend(scan_external(text, source, settings, document, rules))
    return sorted(
        findings, key=lambda item: (item.line, item.column, item.code)
    )
