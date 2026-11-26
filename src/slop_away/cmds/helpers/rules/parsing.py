"""Describe English prose through a parser interface."""

from collections.abc import Iterable
from dataclasses import dataclass
from functools import cache
from string import punctuation
from typing import TYPE_CHECKING, Protocol

from slop_away.utils.markdown import Projection
from slop_away.utils.text import word_matches

SUBJECT = {"nsubj", "nsubjpass", "csubj", "csubjpass", "nsubj:pass"}

if TYPE_CHECKING:
    from spacy.language import Language
    from spacy.tokens import Doc


@dataclass(frozen=True)
class ParsedToken:
    """Hold a word or punctuation mark with language annotations."""

    text: str
    lemma: str
    pos: str
    tag: str
    dependency: str
    index: int
    head: int
    offset: int
    end: int


@dataclass(frozen=True)
class Sentence:
    """Hold sentence text and its language annotations."""

    prose: Projection
    tokens: tuple[ParsedToken, ...]


def is_imperative(sentence: Sentence) -> bool:
    """Check whether a sentence starts with an imperative verb.

    Args:
        sentence: The annotated sentence.

    Returns:
        True for an initial imperative verb without an explicit subject.
    """
    words = [token for token in sentence.tokens if token.pos != "PUNCT"]
    if not words:
        return False
    first = words[0]
    candidate = (
        first.pos == "VERB"
        and first.tag == "VB"
        or first.text.casefold() == "do"
        and first.pos == "AUX"
    )
    head = first.head if first.pos == "AUX" else first.index
    return candidate and not any(
        token.dependency in SUBJECT and token.head == head for token in words
    )


class Parser(Protocol):
    """Supply sentence and word annotations."""

    def prepare(self, projections: Iterable[Projection]) -> None:
        """Analyze prose ahead of parse calls, in one batch.

        Args:
            projections: The prose that later parse calls will receive.
        """
        ...

    def parse(self, projection: Projection) -> tuple[Sentence, ...]:
        """Parse English prose.

        Args:
            projection: The prose with source offsets.

        Returns:
            Sentences and their word annotations.
        """
        ...


@cache
def _model() -> Language:
    """Get the installed English language model.

    Returns:
        The English language model.

    Raises:
        OSError: The required model is not installed.
    """
    import spacy

    return spacy.load("en_core_web_sm", exclude=["ner"])


def prose_text(projection: Projection) -> Projection:
    """Prepare prose for language analysis.

    Args:
        projection: The Markdown prose with source offsets.

    Returns:
        Prose text with its source offsets.
    """
    characters: list[str] = []
    offsets: list[int] = []
    idx = 0
    while idx < len(projection.text):
        char = projection.text[idx]
        if (
            char == "\\"
            and idx + 1 < len(projection.text)
            and projection.text[idx + 1] in punctuation
        ):
            idx += 1
            char = projection.text[idx]
        elif char in "*_~":
            idx += 1
            continue
        elif char in "[]":
            char = " "
        if char.isspace():
            char = " "
            if characters and characters[-1] == " ":
                idx += 1
                continue
        characters.append("'" if char == "’" else char)
        offsets.append(projection.offsets[idx])
        idx += 1
    return Projection("".join(characters), tuple(offsets))


# One analyzed token: text, lemma, part of speech, tag, dependency, index,
# head index, and the start and end of the token in the analyzed text.
_Token = tuple[str, str, str, str, str, int, int, int, int]


_Analysis = tuple[tuple[int, int, tuple[_Token, ...]], ...]
_CACHE: dict[str, _Analysis] = {}
_CACHE_SIZE = 8192


def _remember(text: str, document: Doc) -> _Analysis:
    """Keep the sentences of one analyzed text.

    The result depends only on the text, so a block that a layout edit
    leaves unchanged is not analyzed again.

    Args:
        text: Prose with its whitespace collapsed.
        document: The language model result for the text.

    Returns:
        The start, end, and tokens of each sentence that has words.
    """
    sentences = []
    for span in document.sents:
        start, end = span.start_char, span.end_char
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if not word_matches(text[start:end]):
            continue
        tokens = tuple(
            (
                token.text,
                token.lemma_,
                token.pos_,
                token.tag_,
                token.dep_,
                token.i,
                token.head.i,
                token.idx,
                token.idx + len(token.text) - 1,
            )
            for token in span
            if not token.is_space
        )
        sentences.append((start, end, tokens))
    if len(_CACHE) >= _CACHE_SIZE:
        del _CACHE[next(iter(_CACHE))]
    _CACHE[text] = tuple(sentences)
    return _CACHE[text]


def _analyze(text: str) -> _Analysis:
    """Run the language model on normalized prose, or reuse its result.

    Args:
        text: Prose with its whitespace collapsed.

    Returns:
        The start, end, and tokens of each sentence that has words.
    """
    if text in _CACHE:
        return _CACHE[text]
    return _remember(text, _model()(text))


class SpacyParser:
    """Parse English prose with the installed language model."""

    def prepare(self, projections: Iterable[Projection]) -> None:
        """Analyze prose ahead of parse calls, in one batch.

        A batch runs about twice as fast as one call for each block.

        Args:
            projections: The prose that later parse calls will receive.
        """
        texts = list(
            dict.fromkeys(
                text
                for text in (prose_text(item).text for item in projections)
                if text not in _CACHE and word_matches(text)
            )
        )
        if texts:
            for text, document in zip(
                texts, _model().pipe(texts, batch_size=256), strict=True
            ):
                _remember(text, document)

    def parse(self, projection: Projection) -> tuple[Sentence, ...]:
        """Parse English prose.

        Args:
            projection: The prose with source offsets.

        Returns:
            Sentences and their word annotations.
        """
        plain = prose_text(projection)
        if not word_matches(plain.text):
            return ()
        offsets = plain.offsets
        return tuple(
            Sentence(
                Projection(plain.text[start:end], offsets[start:end]),
                tuple(
                    ParsedToken(
                        text=text,
                        lemma=lemma,
                        pos=pos,
                        tag=tag,
                        dependency=dependency,
                        index=index,
                        head=head,
                        offset=offsets[first],
                        end=offsets[last] + 1,
                    )
                    for (
                        text,
                        lemma,
                        pos,
                        tag,
                        dependency,
                        index,
                        head,
                        first,
                        last,
                    ) in tokens
                ),
            )
            for start, end, tokens in _analyze(plain.text)
        )


PARSER: Parser = SpacyParser()
