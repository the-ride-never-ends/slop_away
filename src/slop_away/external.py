"""Check prose with supported package rules."""

import re
from pathlib import Path
from typing import Any

from slop_away.config import Config
from slop_away.edits import Edit, propose_edit
from slop_away.findings import Finding, make_finding
from slop_away.markdown import Block, Document, Projection
from slop_away.package_types import PackageError
from slop_away.parsing import PARSER, ParsedToken, Sentence, prose_text
from slop_away.rule_schema import Rule, SequenceToken
from slop_away.text import split_sentences


def _scope(block: Block, scope: str) -> bool:
    """Check a block scope.

    Args:
        block: The document block.
        scope: The scope selector.

    Returns:
        True if the block has the required scope.
    """
    kinds = {"text", "raw", "sentence", block.kind}
    if block.kind == "heading":
        kinds.add(f"h{block.level}")
    return set(scope.split(".")) <= kinds


def _scopes(rule: Rule, document: Document) -> list[Projection]:
    """Get the prose ranges for a rule.

    Args:
        rule: The package rule.
        document: The parsed document.

    Returns:
        Prose ranges with source offsets.
    """
    if rule.scopes == ("raw",):
        return [document.prose]
    positive = [scope for scope in rule.scopes if not scope.startswith("~")]
    negative = [scope[1:] for scope in rule.scopes if scope.startswith("~")]
    result = []
    for block in document.blocks:
        matched = [scope for scope in positive if _scope(block, scope)]
        if (
            positive
            and not matched
            or any(_scope(block, scope) for scope in negative)
        ):
            continue
        prose = prose_text(block.prose)
        if any("sentence" in scope.split(".") for scope in matched):
            result.extend(split_sentences(prose))
        else:
            result.append(prose)
    return result


def _message(template: str, values: list[str | int]) -> str:
    """Fill a rule message.

    Args:
        template: The rule message.
        values: The matched values.

    Returns:
        The finding message.

    Raises:
        PackageError: The message requests an absent value.
    """
    index = 0

    def replace(match: re.Match[str]) -> str:
        """Fill one message field.

        Args:
            match: The message field.

        Returns:
            The field text.
        """
        nonlocal index
        if match[0] == "%%":
            return "%"
        if match[1]:
            index = int(match[1]) - 1
        if index >= len(values):
            raise PackageError("Message requests an absent match value.")
        value = values[index]
        index += 1
        return str(value)

    return " ".join(
        re.sub(r"%%|%(?:\[([1-9][0-9]*)\])?[sd]", replace, template).split()
    )


def _except(rule: Rule, text: str) -> bool:
    """Check rule exceptions.

    Args:
        rule: The package rule.
        text: The matched text.

    Returns:
        True if an exception matches.
    """
    return any(pattern.search(text, timeout=1) for pattern in rule.exceptions)


def _matches(
    rule: Rule, prose: Projection
) -> list[tuple[int, str, list[str | int], str]]:
    """Find regular expression rule matches.

    Args:
        rule: The package rule.
        prose: The eligible prose.

    Returns:
        Match offsets, text, message values, and correction hints.
    """
    result: list[tuple[int, str, list[str | int], str]] = []
    for index, pattern in enumerate(rule.patterns):
        matches = [
            match
            for match in pattern.finditer(prose.text, timeout=1)
            if not _except(rule, match[0])
        ]
        if any(match.start() == match.end() for match in matches):
            raise PackageError("Patterns must not produce empty matches.")
        if rule.kind == "occurrence":
            count = len(matches)
            if (
                rule.minimum is not None
                and count < rule.minimum
                or rule.maximum is not None
                and count > rule.maximum
            ):
                start = (
                    matches[0].start()
                    if matches
                    else len(prose.text) - len(prose.text.lstrip())
                )
                if start < len(prose.offsets):
                    result.append(
                        (
                            prose.offsets[start],
                            prose.text.strip(),
                            [count],
                            "Change the number of matches.",
                        )
                    )
            continue
        for match in matches:
            values: list[str | int] = [match[0]]
            hint = (
                "Remove this text."
                if rule.action == "remove"
                else "Revise this text."
            )
            if rule.kind == "substitution":
                replacement = _replacement(match, rule.swaps[index])
                values = [replacement, match[0]]
                hint = f"Use {replacement!r}."
            result.append(
                (prose.offsets[match.start()], prose.text, values, hint)
            )
    return result


def _replacement(match: Any, template: str) -> str:
    """Fill a substitution replacement.

    Args:
        match: The pattern match.
        template: The replacement text.

    Returns:
        The replacement with captured text.
    """
    for field in reversed(list(re.finditer(r"\$(\d+)", template))):
        template = (
            template[: field.start()]
            + (match[int(field[1])] or "")
            + template[field.end() :]
        )
    return template


def swap_edits(
    text: str, document: Document, config: Config, rules: tuple[Rule, ...]
) -> list[Edit]:
    """Propose external word swaps.

    Args:
        text: The source text.
        document: The parsed document.
        config: The document settings.
        rules: The configured rules.

    Returns:
        Source changes with one preferred replacement.

    Raises:
        PackageError: A pattern exceeds its time limit.
    """
    edits = []
    for rule in rules:
        if rule.kind != "substitution" or not config.enabled(rule.code):
            continue
        try:
            for prose in _scopes(rule, document):
                for pattern, template in zip(rule.patterns, rule.swaps):
                    if "|" in template:
                        continue
                    for match in pattern.finditer(prose.text, timeout=1):
                        if _except(rule, match[0]):
                            continue
                        edit = propose_edit(
                            text,
                            prose,
                            match.start(),
                            match.end(),
                            _replacement(match, template),
                        )
                        if edit is not None:
                            edits.append(edit)
        except TimeoutError as error:
            raise PackageError(
                f"{rule.code}: pattern exceeds the time limit."
            ) from error
    return edits


def _accept(condition: SequenceToken, token: ParsedToken) -> bool:
    """Check a sequence token.

    Args:
        condition: The sequence condition.
        token: The parsed word or mark.

    Returns:
        True if the token meets the condition.
    """
    matched = all(
        pattern is None or pattern.fullmatch(value, timeout=1)
        for pattern, value in (
            (condition.pattern, token.text),
            (condition.tag, token.tag),
            (condition.upos, token.pos),
        )
    )
    return not matched if condition.negate else matched


def _sequence(
    rule: Rule, sentence: Sentence
) -> list[tuple[int, str, list[str | int], str]]:
    """Find sequence matches in one sentence.

    Args:
        rule: The sequence rule.
        sentence: The parsed sentence.

    Returns:
        Match offsets, text, message values, and correction hints.

    Raises:
        PackageError: Sequence matching exceeds the operation limit.
    """
    tokens = sentence.tokens
    steps = 0

    def visit(
        index: int, position: int, selected: list[list[ParsedToken]]
    ) -> list[list[ParsedToken]] | None:
        """Find one complete sequence.

        Args:
            index: The condition index.
            position: The next token position.
            selected: The tokens for prior conditions.

        Returns:
            The first complete match, or None.
        """
        nonlocal steps
        steps += 1
        if steps > 100000:
            raise PackageError("Sequence exceeds the operation limit.")
        if index == len(rule.sequence):
            return selected
        condition = rule.sequence[index]
        if (
            condition.negate
            and condition.minimum == 1
            and (
                position == len(tokens)
                and index == len(rule.sequence) - 1
                or position == -1
                and index == 0
            )
        ):
            return visit(index + 1, max(position, 0), selected + [[]])
        pending: list[tuple[int, list[ParsedToken]]] = [(position, [])]
        while pending:
            current, group = pending.pop()
            steps += 1
            if steps > 100000:
                raise PackageError("Sequence exceeds the operation limit.")
            if not 0 <= current < len(tokens) or not _accept(
                condition, tokens[current]
            ):
                continue
            group = group + [tokens[current]]
            following = range(
                current + 1, min(len(tokens), current + 1 + condition.skip) + 1
            )
            if len(group) >= condition.minimum:
                for next_position in following:
                    result = visit(
                        index + 1, next_position, selected + [group]
                    )
                    if result is not None:
                        return result
            if condition.repeat:
                steps += len(following)
                if steps > 100000:
                    raise PackageError("Sequence exceeds the operation limit.")
                pending.extend(
                    (next_position, group)
                    for next_position in reversed(following)
                )
        return None

    results = []
    last = -2
    for start in range(-1 if rule.sequence[0].negate else 0, len(tokens)):
        if start <= last:
            continue
        groups = visit(0, start, [])
        if groups is None:
            continue
        flat = [token for group in groups for token in group]
        if not flat:
            continue
        first, final = flat[0], flat[-1]
        local = sentence.prose.offsets.index(first.offset)
        if any(
            match.start() <= local < match.end()
            for pattern in rule.exceptions
            for match in pattern.finditer(sentence.prose.text, timeout=1)
        ):
            continue
        targets = [
            token
            for condition, group in zip(rule.sequence, groups)
            if condition.target
            for token in group
        ]
        shown = targets or flat
        values: list[str | int] = [
            " ".join(token.text for token in group) for group in groups
        ]
        results.append(
            (
                shown[0].offset,
                sentence.prose.text,
                values,
                "Revise this phrase.",
            )
        )
        last = tokens.index(final)
    return results


def scan_external(
    text: str,
    path: Path,
    config: Config,
    document: Document,
    rules: tuple[Rule, ...],
) -> list[Finding]:
    """Check visible prose with package rules.

    Args:
        text: The Markdown source.
        path: The source path.
        config: The settings for this path.
        document: The parsed document.
        rules: The configured package rules.

    Returns:
        The package findings.

    Raises:
        PackageError: A rule cannot be applied within its limits.
    """
    findings = []
    sentences: dict[Projection, tuple[Sentence, ...]] = {}
    for rule in rules:
        if not config.enabled(rule.code):
            continue
        try:
            matches: list[tuple[int, str, list[str | int], str]] = []
            for prose in _scopes(rule, document):
                if rule.kind == "sequence":
                    if prose not in sentences:
                        sentences[prose] = PARSER.parse(prose)
                    matches.extend(
                        match
                        for sentence in sentences[prose]
                        for match in _sequence(rule, sentence)
                    )
                else:
                    matches.extend(_matches(rule, prose))
            seen: set[int] = set()
            for offset, context, values, hint in sorted(matches):
                if offset in seen:
                    continue
                if rule.limit is not None and len(seen) >= rule.limit:
                    break
                seen.add(offset)
                findings.append(
                    make_finding(
                        rule.code,
                        offset,
                        text,
                        path,
                        context,
                        _message(rule.message, values),
                        hint,
                    )
                )
        except (TimeoutError, IndexError, PackageError) as error:
            raise PackageError(f"{rule.code}: {error}") from error
    return findings
