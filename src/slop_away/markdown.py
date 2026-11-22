"""Extract Markdown text with source locations."""

import html
import re
from dataclasses import dataclass

from markdown_it import MarkdownIt
from markdown_it.helpers import parseLinkDestination, parseLinkTitle
from markdown_it.token import Token
from mdit_py_plugins.front_matter import front_matter_plugin

COMMENT = re.compile(r"(?<!\\)<!--[\s\S]*?(?:-->|\Z)")
INLINE = re.compile(
    r"(?P<comment>(?<!\\)<!--[\s\S]*?(?:-->|\Z))"
    r"|(?P<code>(?<![\\`])(?P<ticks>`+)(?!`)"
    r"[\s\S]*?(?<!`)(?P=ticks)(?!`))"
)
URL = re.compile(r"(?:https?://|mailto:|www\.)[^\s<>]+", re.IGNORECASE)
ENTITY = re.compile(r"&(?:#\d+|#x[0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]+);")
TAG = re.compile(r"</?[A-Za-z][^<>]*?>")


@dataclass(frozen=True)
class Projection:
    """Hold text and its source offsets."""

    text: str
    offsets: tuple[int, ...]


@dataclass(frozen=True)
class Block:
    """Hold a block of visible document text."""

    kind: str
    level: int
    offset: int
    prose: Projection


@dataclass(frozen=True)
class Document:
    """Hold visible text and HTML comments."""

    prose: Projection
    comments: tuple[Projection, ...]
    blocks: tuple[Block, ...]


def _mask(characters: list[str], start: int, end: int) -> None:
    """Exclude a text range.

    Args:
        characters: The source characters.
        start: The first source offset.
        end: The offset after the range.
    """
    for index in range(start, end):
        if characters[index] not in "\r\n":
            characters[index] = " "


def _project(text: str, start: int = 0) -> Projection:
    """Map text to its source.

    Args:
        text: The source text.
        start: The first source offset.

    Returns:
        Text with source offsets for each character.
    """
    characters: list[str] = []
    offsets: list[int] = []
    cursor = 0
    for match in ENTITY.finditer(text):
        characters.extend(text[cursor : match.start()])
        offsets.extend(range(start + cursor, start + match.start()))
        decoded = html.unescape(match.group())
        characters.extend(decoded)
        offsets.extend([start + match.start()] * len(decoded))
        cursor = match.end()
    characters.extend(text[cursor:])
    offsets.extend(range(start + cursor, start + len(text)))
    return Projection("".join(characters), tuple(offsets))


def _destinations(characters: list[str]) -> None:
    """Exclude link destinations.

    Args:
        characters: The source characters.
    """
    source = "".join(characters)
    for match in re.finditer(r"\]\(", source):
        start = match.end()
        while start < len(source) and source[start].isspace():
            start += 1
        result = parseLinkDestination(source, start, len(source))
        if not result.ok:
            continue
        end = result.pos
        while end < len(source) and source[end].isspace():
            end += 1
        if end < len(source) and source[end] in "\"'":
            title = parseLinkTitle(source, end, len(source))
            if not title.ok:
                continue
            end = title.pos
            while end < len(source) and source[end].isspace():
                end += 1
        if end < len(source) and source[end] == ")":
            _mask(characters, match.start() + 1, end + 1)


def _comment(text: str, start: int) -> Projection:
    """Map an HTML comment to its source.

    Args:
        text: The HTML comment.
        start: The source offset.

    Returns:
        The comment text with its source offsets.
    """
    body = text[4:-3] if text.endswith("-->") else text[4:]
    return _project(body, start + 4)


def _blocks(
    tokens: list[Token], starts: list[int], characters: list[str]
) -> tuple[Block, ...]:
    """Group visible text by document block.

    Args:
        tokens: The Markdown blocks.
        starts: The source line offsets.
        characters: The visible source characters.

    Returns:
        The document blocks with source offsets.
    """
    result = []
    depth = 0
    kind = "paragraph"
    level = 0
    for token in tokens:
        if token.type in {"bullet_list_open", "ordered_list_open"}:
            depth += 1
        elif token.type in {"bullet_list_close", "ordered_list_close"}:
            depth -= 1
        elif token.type == "paragraph_open":
            kind, level = ("list" if depth else "paragraph"), 0
        elif token.type == "heading_open":
            kind, level = "heading", int(token.tag[1:])
        if token.type not in {"inline", "html_block"} or token.map is None:
            continue
        start, end = (starts[index] for index in token.map)
        visible = characters[start:end].copy()
        block_kind = (
            "list"
            if depth
            else "paragraph"
            if token.type == "html_block"
            else kind
        )
        prefix = r"(?m)^[ \t]*(?:>[ \t]*)*"
        if block_kind == "heading":
            prefix += r"(?:#{1,6}[ \t]+)?"
        elif block_kind == "list":
            prefix += r"(?:[-*+]|\d+[.)])[ \t]+(?:\[[ xX]\][ \t]+)?"
        for match in re.finditer(prefix, "".join(visible)):
            _mask(visible, match.start(), match.end())
        result.append(
            Block(
                block_kind,
                level if block_kind == "heading" else 0,
                start,
                _project("".join(visible), start),
            )
        )
    return tuple(result)


def parse_document(text: str) -> Document:
    """Extract the text that rules can check.

    Args:
        text: The Markdown source.

    Returns:
        Visible text and HTML comments with source offsets.
    """
    parser = MarkdownIt("gfm-like").use(front_matter_plugin)
    tokens = parser.parse(text)
    starts = [0] + [match.end() for match in re.finditer(r"\r\n|\r|\n", text)]
    if starts[-1] != len(text):
        starts.append(len(text))
    characters = [char if char in "\r\n" else " " for char in text]
    inline_ranges = []
    for token in tokens:
        if token.type in {"inline", "html_block"} and token.map is not None:
            start, end = (starts[index] for index in token.map)
            characters[start:end] = text[start:end]
            if token.type == "inline":
                inline_ranges.append((start, end))
    for token in tokens:
        if token.type == "table_open" and token.map is not None:
            _mask(characters, *(starts[index] for index in token.map))
    comments = []
    for start, end in inline_ranges:
        source = "".join(characters[start:end])
        for match in INLINE.finditer(source):
            if match.group("comment") is not None:
                comments.append(_comment(match.group(), start + match.start()))
            _mask(characters, start + match.start(), start + match.end())
    for match in COMMENT.finditer("".join(characters)):
        comments.append(_comment(match.group(), match.start()))
        _mask(characters, match.start(), match.end())
    _destinations(characters)
    for match in TAG.finditer("".join(characters)):
        _mask(characters, match.start(), match.end())
    source = "".join(characters)
    for match in URL.finditer(source):
        end = match.end()
        while end > match.start() and source[end - 1] in ".,;:!?)":
            end -= 1
        _mask(characters, match.start(), end)
    return Document(
        _project("".join(characters)),
        tuple(comments),
        _blocks(tokens, starts, characters),
    )
