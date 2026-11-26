"""Read supported Vale rule definitions."""

import re
from dataclasses import dataclass
from typing import Any

import regex  # type: ignore[import-untyped]
import yaml  # type: ignore[import-untyped]

from slop_away.utils.exceptions import PackageError


class RuleLoader(yaml.SafeLoader):
    """Read rule data without duplicate keys."""

    def construct_mapping(self, node: Any, deep: bool = False) -> Any:
        """Read a rule mapping.

        Args:
            node: The mapping node.
            deep: Read child nodes in full.

        Returns:
            The mapping.

        Raises:
            ValueError: A key occurs twice.
        """
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in result:
                raise ValueError("Rule keys must be unique strings.")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


@dataclass(frozen=True)
class SequenceToken:
    """Hold one sequence condition."""

    pattern: Any = None
    tag: Any = None
    upos: Any = None
    negate: bool = False
    skip: int = 0
    minimum: int = 1
    target: bool = False
    repeat: bool = False


@dataclass(frozen=True)
class Rule:
    """Hold a checked rule definition."""

    code: str
    kind: str
    message: str
    scopes: tuple[str, ...]
    patterns: tuple[Any, ...]
    swaps: tuple[str, ...]
    sequence: tuple[SequenceToken, ...]
    exceptions: tuple[Any, ...]
    minimum: int | None
    maximum: int | None
    limit: int | None
    action: str


def _strings(value: Any) -> list[str]:
    """Check a string list.

    Args:
        value: The list.

    Returns:
        The checked list.

    Raises:
        ValueError: The list is invalid.
    """
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ValueError("Expected a nonempty string list.")
    return value


def _integer(value: Any, minimum: int = 0) -> int:
    """Check an integer limit.

    Args:
        value: The limit.
        minimum: The smallest permitted value.

    Returns:
        The checked limit.

    Raises:
        ValueError: The limit is invalid.
    """
    if type(value) is not int or value < minimum:
        raise ValueError(f"Expected an integer of at least {minimum}.")
    return value


def _compile(value: Any, flags: int, bounded: bool = False) -> Any:
    """Check a rule pattern.

    Args:
        value: The pattern.
        flags: The matching flags.
        bounded: Require word boundaries and permit wrapped text.

    Returns:
        The compiled pattern.

    Raises:
        ValueError: The pattern is invalid or matches empty text.
    """
    if not isinstance(value, str) or not value:
        raise ValueError("Expected a nonempty pattern.")
    if regex.compile(value, flags).search("", timeout=1) is not None:
        raise ValueError("Patterns must not match empty text.")
    if bounded:
        value = re.sub(r"(\\.|\[[^\]]*\])| +", lambda m: m[1] or r"\s+", value)
        value = rf"\b(?:{value})\b"
    pattern = regex.compile(value, flags)
    if pattern.search("", timeout=1) is not None:
        raise ValueError("Patterns must not match empty text.")
    return pattern


def _token(value: Any, flags: int) -> SequenceToken:
    """Check one sequence condition.

    Args:
        value: The condition mapping.
        flags: The matching flags.

    Returns:
        The checked condition.

    Raises:
        ValueError: A condition field is invalid.
    """
    allowed = {"pattern", "tag", "upos", "negate", "skip", "min", "target"}
    if not isinstance(value, dict) or value.keys() - allowed:
        raise ValueError("Unsupported sequence fields.")
    if not value.keys() & {"pattern", "tag", "upos"}:
        raise ValueError("Sequence tokens need a pattern or word class.")
    for key in ("negate", "target"):
        if key in value and type(value[key]) is not bool:
            raise ValueError(f"{key}: expected a boolean.")
    return SequenceToken(
        _compile(value["pattern"], flags) if "pattern" in value else None,
        _compile(value["tag"], flags) if "tag" in value else None,
        _compile(value["upos"], flags) if "upos" in value else None,
        value.get("negate", False),
        _integer(value.get("skip", 0)),
        _integer(value.get("min", 1), 1),
        value.get("target", False),
        "min" in value,
    )


def read_rule(code: str, src: bytes) -> Rule:
    """Read a supported Vale rule.

    Args:
        code: The package and rule name.
        src: The UTF-8 YAML rule.

    Returns:
        The checked rule.

    Raises:
        PackageError: The rule is invalid or unsupported.
    """
    try:
        return _read(code, src)
    except (
        ValueError,
        TypeError,
        yaml.YAMLError,
        regex.error,
        TimeoutError,
    ) as error:
        raise PackageError(f"{code}: {error}") from error


def _read(code: str, src: bytes) -> Rule:
    """Check the rule fields.

    Args:
        code: The rule code.
        src: The YAML rule.

    Returns:
        The checked rule.

    Raises:
        ValueError: A rule field is invalid.
    """
    documents = [
        item
        for item in yaml.load_all(src.decode("utf-8"), Loader=RuleLoader)
        if item is not None
    ]
    if len(documents) != 1 or not isinstance(documents[0], dict):
        raise ValueError("Expected one rule mapping.")
    data = documents[0]
    kind = data.get("extends")
    fields = {
        "existence": {"tokens", "raw", "append", "nonword"},
        "substitution": {"swap", "nonword"},
        "occurrence": {"token", "min", "max"},
        "sequence": {"tokens"},
    }
    common = {
        "extends",
        "message",
        "scope",
        "ignorecase",
        "exceptions",
        "level",
        "link",
        "description",
        "action",
        "limit",
    }
    if not isinstance(kind, str) or kind not in fields:
        raise ValueError(f"Unsupported rule type {kind!r}.")
    if data.keys() - (common | fields[kind]):
        raise ValueError(
            f"Unsupported fields: {sorted(data.keys() - (common | fields[kind]))}."
        )
    for key in ("ignorecase", "nonword", "append"):
        if key in data and type(data[key]) is not bool:
            raise ValueError(f"{key}: expected a boolean.")
    message = data.get("message")
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Expected a nonempty message.")
    remainder = re.sub(r"%%|%(?:\[[1-9][0-9]*\])?[sd]", "", message)
    if "%" in remainder:
        raise ValueError("Unsupported message format.")
    if data.get("level", "error") not in {"error", "warning", "suggestion"}:
        raise ValueError("Unsupported rule level.")
    for key in ("link", "description"):
        if key in data and not isinstance(data[key], str):
            raise ValueError(f"{key}: expected text.")
    scopes = data.get("scope", "text")
    scopes = _strings([scopes] if isinstance(scopes, str) else scopes)
    allowed = {
        "text",
        "raw",
        "sentence",
        "paragraph",
        "heading",
        "list",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
    }
    for scope in scopes:
        if not set(scope.removeprefix("~").split(".")) <= allowed:
            raise ValueError(f"Unsupported scope {scope!r}.")
    action = data.get("action", {})
    if not isinstance(action, dict) or action.keys() - {"name"}:
        raise ValueError("Unsupported action fields.")
    if action and action.get("name") not in {"replace", "remove"}:
        raise ValueError("Unsupported rule action.")
    flags = regex.MULTILINE | (regex.IGNORECASE if data.get("ignorecase") else 0)
    bounded = not data.get("nonword", False)
    patterns: list[Any] = []
    swaps: tuple[str, ...] = ()
    sequence: tuple[SequenceToken, ...] = ()
    minimum = maximum = None
    if kind == "existence":
        tokens = _strings(data["tokens"]) if "tokens" in data else []
        raw = "".join(_strings(data["raw"])) if "raw" in data else ""
        normal = "|".join(f"(?:{token})" for token in tokens)
        if normal:
            normal = _compile(normal, flags, bounded).pattern
        pattern = normal + raw if data.get("append", True) else raw + normal
        patterns.append(_compile(pattern, flags))
    elif kind == "substitution":
        swap = data.get("swap")
        if (
            not isinstance(swap, dict)
            or not swap
            or any(not isinstance(v, str) or not v for v in swap.values())
        ):
            raise ValueError("Expected nonempty substitution pairs.")
        patterns.extend(_compile(key, flags, bounded) for key in swap)
        swaps = tuple(swap.values())
    elif kind == "occurrence":
        patterns.append(_compile(data.get("token"), flags))
        minimum = _integer(data["min"]) if "min" in data else None
        maximum = _integer(data["max"]) if "max" in data else None
        if (
            minimum is None
            and maximum is None
            or minimum is not None
            and maximum is not None
            and minimum > maximum
        ):
            raise ValueError("Expected consistent occurrence limits.")
    else:
        conditions = data.get("tokens")
        if not isinstance(conditions, list) or not conditions or len(conditions) > 64:
            raise ValueError("Expected 1 to 64 sequence tokens.")
        sequence = tuple(_token(token, flags) for token in conditions)
        if not any(token.pattern is not None for token in sequence):
            raise ValueError("A sequence needs a text pattern.")
    exceptions = (
        tuple(_compile(item, flags) for item in _strings(data["exceptions"]))
        if "exceptions" in data
        else ()
    )
    limit = _integer(data["limit"], 1) if "limit" in data else None
    available = len(sequence) if kind == "sequence" else 2 if swaps else 1
    index = 0
    for field in re.finditer(r"%%|%(?:\[([1-9][0-9]*)\])?[sd]", message):
        if field[0] == "%%":
            continue
        index = int(field[1]) - 1 if field[1] else index
        if index >= available:
            raise ValueError("Message requests an absent match value.")
        index += 1
    for pattern, replacement in zip(patterns, swaps):
        if any(
            int(field[1]) > pattern.groups
            for field in re.finditer(r"\$(\d+)", replacement)
        ):
            raise ValueError("Replacement requests an absent capture group.")
    return Rule(
        code=code,
        kind=kind,
        message=message,
        scopes=tuple(scopes),
        patterns=tuple(patterns),
        swaps=swaps,
        sequence=sequence,
        exceptions=exceptions,
        minimum=minimum,
        maximum=maximum,
        limit=limit,
        action=action.get("name", ""),
    )
