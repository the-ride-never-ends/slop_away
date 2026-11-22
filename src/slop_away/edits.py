"""Describe changes to source text."""

from dataclasses import dataclass

from slop_away.markdown import Projection


@dataclass(frozen=True, order=True)
class Edit:
    """Hold one source replacement."""

    start: int
    end: int
    replacement: str


def propose_edit(
    text: str, prose: Projection, start: int, end: int, replacement: str
) -> Edit | None:
    """Describe a change to a visible source range.

    Args:
        text: The source text.
        prose: The visible prose with source offsets.
        start: The first prose offset.
        end: The prose offset after the range.
        replacement: The replacement text.

    Returns:
        A source change, or None if the range is not direct source text.
    """
    offsets = prose.offsets[start:end]
    if not offsets:
        return None
    left, right = offsets[0], offsets[-1] + 1
    if (
        offsets != tuple(range(left, right))
        or text[left:right] != prose.text[start:end]
    ):
        return None
    return Edit(left, right, replacement)
