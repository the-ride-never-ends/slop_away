"""Apply supported changes to Markdown source."""

import re
from itertools import pairwise
from pathlib import Path

from slop_away.cmds.helpers.external import swap_edits
from slop_away.cmds.helpers.packages import load_rules
from slop_away.cmds.helpers.rules.schema import Rule
from slop_away.cmds.helpers.rules.verbosity import FILLER
from slop_away.config import Config
from slop_away.utils.edits import Edit, propose_edit
from slop_away.utils.markdown import Document, parse_document
from slop_away.utils.text import word_matches

NEGATIVES = {
    "aren't": "are not",
    "can't": "cannot",
    "couldn't": "could not",
    "didn't": "did not",
    "doesn't": "does not",
    "don't": "do not",
    "hadn't": "had not",
    "hasn't": "has not",
    "haven't": "have not",
    "isn't": "is not",
    "mightn't": "might not",
    "mustn't": "must not",
    "needn't": "need not",
    "shan't": "shall not",
    "shouldn't": "should not",
    "wasn't": "was not",
    "weren't": "were not",
    "won't": "will not",
    "wouldn't": "would not",
    "let's": "let us",
}
HIDDEN = frozenset(
    "\u200b\ufeff\u202a\u202b\u202c\u202d\u202e"
    "\u2066\u2067\u2068\u2069\u200e\u200f\u061c"
)

SUFFIX_EXPANSION_SUBJECTS = (
    ("'re", " are", {"you", "we", "they"}),
    (
        "'ve",
        " have",
        {
            "i",
            "you",
            "we",
            "they",
            "could",
            "should",
            "would",
            "might",
            "must",
        },
    ),
    (
        "'ll",
        " will",
        {
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "who",
            "what",
            "there",
        },
    ),
)


def _case(original: str, replacement: str) -> str:
    """Keep the source capitalization.

    Args:
        original: The original phrase.
        replacement: The preferred phrase.

    Returns:
        The replacement with source capitalization.
    """
    if original.isupper():
        return replacement.upper()
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def _expansion(word: str) -> str | None:
    """Get an unambiguous contraction expansion.

    Args:
        word: The source word.

    Returns:
        The expansion, or None if no safe expansion is defined.
    """
    normalized = word.casefold().replace("’", "'")
    if normalized in NEGATIVES:
        return _case(word, NEGATIVES[normalized])
    if normalized == "i'm":
        return "I AM" if word.isupper() else "I am"
    for suffix, expansion, subjects in SUFFIX_EXPANSION_SUBJECTS:
        subject = normalized.removesuffix(suffix)
        if normalized.endswith(suffix) and subject in subjects:
            preferred = ("I" if subject == "i" else subject) + expansion
            return _case(word, preferred)
    return None


def _native(text: str, doc: Document, config: Config) -> list[Edit]:
    """Find native prose fixes.

    Args:
        text: The source text.
        doc: The parsed document.
        config: The document settings.

    Returns:
        The proposed fixes.
    """
    edits = []
    for block in doc.blocks:
        prose = block.prose
        for match in re.finditer(r"(?<=\S)[ \t]{2,}(?=\S)", prose.text):
            edit = propose_edit(
                text=text,
                prose=prose,
                start=match.start(),
                end=match.end(),
                replacement=" ",
            )
            if edit is not None:
                edits.append(edit)
        if config.enabled("STE004"):
            for match in word_matches(prose.text):
                expansion = _expansion(match[0])
                if expansion is not None:
                    edit = propose_edit(
                        text=text,
                        prose=prose,
                        start=match.start(),
                        end=match.end(),
                        replacement=expansion,
                    )
                    if edit is not None:
                        edits.append(edit)
        if block.kind == "heading":
            line = text[block.offset :].splitlines()[0]
            marker = re.match(r"[ ]{0,3}#{1,6}([ \t]+)(?=\S)", line)
            if marker and marker[1] != " ":
                edits.append(
                    Edit(
                        block.offset + marker.start(1),
                        block.offset + marker.end(1),
                        " ",
                    )
                )
    return edits


def _unsafe(text: str, doc: Document, config: Config) -> list[Edit]:
    """Find native changes that can change meaning.

    Args:
        text: The source text.
        doc: The parsed document.
        config: The document settings.

    Returns:
        The proposed unsafe fixes.
    """
    edits = []
    for block in doc.blocks:
        prose = block.prose
        if config.enabled("VRB001"):
            for match in FILLER.finditer(prose.text):
                if any(char in match[0] for char in "*_~"):
                    continue
                replacement = "to" if match[0].casefold().startswith("in") else ""
                end = match.end()
                if not replacement:
                    while end < len(prose.text) and prose.text[end] in " \t":
                        end += 1
                prefix = prose.text[: match.start()].rstrip()
                initial = not prefix or prefix[-1] in ".!?"
                if replacement:
                    replacement = _case(match[0], replacement)
                elif initial and end < len(prose.text) and prose.text[end].isalpha():
                    replacement = prose.text[end].upper()
                    end += 1
                edit = propose_edit(
                    text=text,
                    prose=prose,
                    start=match.start(),
                    end=end,
                    replacement=replacement,
                )
                if edit is not None:
                    edits.append(edit)
        if config.enabled("STE007"):
            for preferred, synonyms in config.glossary.items():
                for synonym in synonyms:
                    pattern = re.compile(
                        r"(?<!\w)"
                        + r"\s+".join(re.escape(part) for part in synonym.split())
                        + r"(?!\w)",
                        re.IGNORECASE,
                    )
                    for match in pattern.finditer(prose.text):
                        edit = propose_edit(
                            text=text,
                            prose=prose,
                            start=match.start(),
                            end=match.end(),
                            replacement=_case(match[0], preferred),
                        )
                        if edit is not None:
                            edits.append(edit)
    return edits


def fix_text(
    *,
    text: str,
    path: Path,
    config: Config,
    unsafe: bool,
    rules: tuple[Rule, ...],
) -> str:
    """Apply selected fixes to one document.

    Args:
        text: The Markdown source.
        path: The source path.
        config: The project settings.
        unsafe: Permit changes that can change meaning.
        rules: The configured package rules.

    Returns:
        The changed source text.

    Raises:
        ValueError: The fix plan contains conflicting changes or a cycle.
    """
    settings = config.for_path(path)
    seen = {text}
    for _ in range(20):
        doc = parse_document(text)
        edits: list[Edit] = []
        if settings.enabled("INJ004"):
            for prose in (doc.prose, *doc.comments):
                for idx, character in enumerate(prose.text):
                    if character in HIDDEN:
                        edit = propose_edit(
                            text=text,
                            prose=prose,
                            start=idx,
                            end=idx + 1,
                            replacement="",
                        )
                        if edit is not None:
                            edits.append(edit)
        if path.name not in settings.instruction_files and not edits:
            edits.extend(_native(text, doc, settings))
            if unsafe and not edits:
                edits.extend(_unsafe(text, doc, settings))
                edits.extend(
                    swap_edits(text=text, doc=doc, config=settings, rules=rules)
                )
        ordered = sorted(
            {edit for edit in edits if text[edit.start : edit.end] != edit.replacement}
        )
        if not ordered:
            return text
        for left, right in pairwise(ordered):
            if left.end > right.start:
                raise ValueError("Fixes overlap; select one rule before fixing.")
        result = text
        for edit in reversed(ordered):
            result = result[: edit.start] + edit.replacement + result[edit.end :]
        if result in seen:
            raise ValueError("Fixes form a cycle; change the selected rules.")
        seen.add(result)
        text = result
    raise ValueError("Fixes exceed the limit of 20 passes.")


def apply_fixes(
    *, text: str, path: str | Path, config: Config, unsafe: bool = False
) -> str:
    """Apply supported fixes to Markdown text.

    Args:
        text: The Markdown source.
        path: The source path.
        config: The project settings.
        unsafe: Permit changes that can change meaning.

    Returns:
        The changed Markdown source.

    Raises:
        ValueError: An input, package cache, or fix plan is invalid.
    """
    return fix_text(
        text=text,
        path=Path(path),
        config=config,
        unsafe=unsafe,
        rules=load_rules(config),
    )
