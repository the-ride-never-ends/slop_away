"""Supply corpus prose and edits that keep its meaning."""

import json
import re
import textwrap
from pathlib import Path

from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin

from slop_away import Config, check_text
from slop_away.cmds.helpers.rules.parsing import prose_text
from slop_away.utils.markdown import parse_document
from slop_away.utils.text import split_sentences, word_matches
from tests.corpus_support import CORPUS_ROOT

EXTERNAL = json.loads((CORPUS_ROOT / "external/sources.json").read_text())
DOCUMENTS = tuple(
    (path, path.name)
    for group in ("fixed", "good")
    for path in sorted((CORPUS_ROOT / group).glob("*.md"))
) + tuple(
    (CORPUS_ROOT / "external" / item["file"], Path(item["path"]).name)
    for item in EXTERNAL["documents"]
)


def sentences():
    """Get clean sentences from each corpus group.

    Returns:
        Distinct sentences with eight to sixteen words.

    Raises:
        ValueError: A corpus group has no clean sentences.
    """
    result = set()
    for group in ("fixed", "good", "external"):
        values = set()
        for path, _logical in DOCUMENTS:
            if path.parent.name != group:
                continue
            document = parse_document(path.read_text())
            for block in document.blocks:
                if block.kind == "heading":
                    continue
                for sentence in split_sentences(prose_text(block.prose)):
                    text = " ".join(sentence.text.split())
                    if 8 <= len(word_matches(text)) <= 16 and re.fullmatch(
                        r"[A-Za-z ,;'-]+[.!?]", text
                    ):
                        values.add(text)
        clean = [
            text
            for text in sorted(values)
            if not check_text("- " + text, "sample.md", Config())
        ]
        if not clean:
            raise ValueError(f"No clean sentences in {group}.")
        result.update(clean)
    return tuple(sorted(result))


def transform(text, operation, width):
    """Change document layout without a prose edit.

    Args:
        text: The source document.
        operation: The layout edit.
        width: The line width for paragraphs.

    Returns:
        The document with its changed layout.

    Raises:
        ValueError: The operation is unknown.
    """
    if operation not in {"wrap", "markers", "blanks", "sections"}:
        raise ValueError(f"Unknown layout operation {operation!r}.")
    lines = text.splitlines(keepends=True)
    tokens = MarkdownIt("gfm-like").use(front_matter_plugin).parse(text)
    edits = []
    if operation == "wrap":
        for token in tokens:
            if token.type != "paragraph_open" or token.level or not token.map:
                continue
            start, end = token.map
            source = "".join(lines[start:end])
            if (
                "  \n" in source
                or not re.fullmatch(r"[A-Za-z0-9 ,.;:'!?()\-\n]+", source)
                or re.search(r"(?:^|\s)[-+*](?:\s|$)", source)
            ):
                continue
            edits.append(
                (
                    start,
                    end,
                    textwrap.fill(
                        source,
                        width=width,
                        break_long_words=False,
                        break_on_hyphens=False,
                    )
                    + "\n",
                )
            )
    elif operation == "markers":
        for token in tokens:
            if token.type == "list_item_open" and token.markup in {"-", "*", "+"}:
                start = token.map[0]
                edits.append(
                    (start, start + 1, re.sub(r"^(\s*)[-*+] ", r"\1+ ", lines[start]))
                )
    elif operation == "blanks":
        starts = {
            token.map[0]
            for token in tokens
            if token.map
            and token.level == 0
            and token.nesting != -1
            and token.type != "front_matter"
        }
        edits = [(start, start, "\n" * (width % 3 + 1)) for start in starts]
    else:
        boundaries = [
            token.map[0]
            for token in tokens
            if token.type == "heading_open"
            and token.tag in {"h1", "h2"}
            and token.level == 0
        ]
        headings = {
            token.map[0]: token.tag
            for token in tokens
            if token.type == "heading_open"
            and token.tag in {"h1", "h2"}
            and token.level == 0
        }
        groups, group = [], []
        for start in boundaries:
            if headings[start] == "h1":
                if group:
                    groups.append((group, start))
                group = []
            else:
                group.append(start)
        if group:
            groups.append((group, len(lines)))
        for starts, end in groups:
            sections = [
                "".join(lines[left:right])
                for left, right in zip(starts, [*starts[1:], end], strict=True)
            ]
            if len(sections) > 1:
                edits.append((starts[0], end, "\n\n".join(reversed(sections))))
    for start, end, source in sorted(edits, reverse=True):
        lines[start:end] = [source]
    return "".join(lines)
