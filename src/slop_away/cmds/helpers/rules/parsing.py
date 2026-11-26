"""Describe English prose through a parser interface."""

from dataclasses import dataclass
from functools import cache
from string import punctuation
from typing import TYPE_CHECKING, Protocol

from slop_away.utils.markdown import Projection
from slop_away.utils.text import word_matches

SUBJECT = {"nsubj", "nsubjpass", "csubj", "csubjpass", "nsubj:pass"}

if TYPE_CHECKING:
    from spacy.language import Language


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


class SpacyParser:
    """Parse English prose with the installed language model."""

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
        document = _model()(plain.text)
        sentences = []
        for span in document.sents:
            start, end = span.start_char, span.end_char
            while start < end and plain.text[start].isspace():
                start += 1
            while end > start and plain.text[end - 1].isspace():
                end -= 1
            prose = Projection(plain.text[start:end], plain.offsets[start:end])
            if not word_matches(prose.text):
                continue
            tokens = tuple(
                ParsedToken(
                    text=token.text,
                    lemma=token.lemma_,
                    pos=token.pos_,
                    tag=token.tag_,
                    dependency=token.dep_,
                    index=token.i,
                    head=token.head.i,
                    offset=plain.offsets[token.idx],
                    end=plain.offsets[token.idx + len(token.text) - 1] + 1,
                )
                for token in span
                if not token.is_space
            )
            sentences.append(Sentence(prose, tokens))
        return tuple(sentences)


PARSER: Parser = SpacyParser()
