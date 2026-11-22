"""Read and write finding baselines."""

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

from slop_away.findings import Finding
from slop_away.storage import write_text

FILENAME = "slop_away.baseline.json"


def _fingerprint(value: str) -> None:
    """Check a baseline fingerprint.

    Args:
        value: The finding fingerprint.

    Raises:
        ValueError: The fingerprint is invalid.
    """
    code, separator, remainder = value.partition(":")
    path, boundary, digest = remainder.rpartition(":")
    relative = PurePosixPath(path)
    if (
        not separator
        or not boundary
        or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*", code)
        or not path
        or relative.is_absolute()
        or ".." in relative.parts
        or relative.as_posix() != path
        or path == "."
        or not re.fullmatch(r"[0-9a-f]{64}", digest)
    ):
        raise ValueError("Invalid finding fingerprint.")


@dataclass(frozen=True)
class Baseline:
    """Hold known finding fingerprints."""

    fingerprints: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        """Check the baseline records.

        Raises:
            TypeError: The records have the wrong type.
            ValueError: A fingerprint is invalid.
        """
        if not isinstance(self.fingerprints, frozenset) or any(
            not isinstance(value, str) for value in self.fingerprints
        ):
            raise TypeError("Expected a frozenset of fingerprint strings.")
        for value in self.fingerprints:
            _fingerprint(value)

    @classmethod
    def build(cls, findings: Iterable[Finding]) -> Baseline:
        """Build a baseline from findings.

        Args:
            findings: The known findings.

        Returns:
            Their baseline.

        Raises:
            ValueError: A finding fingerprint is invalid.
        """
        return cls(frozenset(finding.fingerprint for finding in findings))

    def matches(self, finding: Finding) -> bool:
        """Check whether a finding is known.

        Args:
            finding: The finding to check.

        Returns:
            True if its fingerprint is in the baseline.
        """
        return finding.fingerprint in self.fingerprints


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Read unique JSON fields.

    Args:
        pairs: The JSON field names and values.

    Returns:
        The JSON object.

    Raises:
        ValueError: A field occurs twice.
    """
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate baseline field {key!r}.")
        result[key] = value
    return result


def load_baseline(root: str | Path) -> Baseline:
    """Read the project baseline.

    Args:
        root: The project directory.

    Returns:
        The stored baseline, or an empty baseline if the file is absent.

    Raises:
        OSError: The baseline cannot be read.
        ValueError: The directory or baseline is invalid.
    """
    directory = Path(root)
    if not directory.is_dir():
        raise ValueError(f"{directory}: expected a project directory.")
    path = directory / FILENAME
    try:
        source = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return Baseline()
    except UnicodeError as error:
        raise ValueError(f"{path}: {error}") from error
    try:
        data = json.loads(source, object_pairs_hook=_object)
        if (
            not isinstance(data, dict)
            or data.keys() != {"version", "fingerprints"}
            or type(data["version"]) is not int
            or data["version"] != 1
        ):
            raise ValueError("Expected baseline version 1 and fingerprints.")
        values = data["fingerprints"]
        if (
            not isinstance(values, list)
            or any(not isinstance(value, str) for value in values)
            or len(set(values)) != len(values)
        ):
            raise ValueError("Expected unique fingerprint strings.")
        return Baseline(frozenset(values))
    except ValueError as error:
        raise ValueError(f"{path}: {error}") from error


def write_baseline(root: str | Path, findings: Iterable[Finding]) -> Baseline:
    """Replace the project baseline with the supplied findings.

    Args:
        root: The project directory.
        findings: The findings to record.

    Returns:
        The new baseline.

    Raises:
        OSError: The baseline cannot be written.
        ValueError: The directory or a finding fingerprint is invalid.
    """
    directory = Path(root)
    if not directory.is_dir():
        raise ValueError(f"{directory}: expected a project directory.")
    baseline = Baseline.build(findings)
    source = (
        json.dumps(
            {"version": 1, "fingerprints": sorted(baseline.fingerprints)},
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    write_text(directory / FILENAME, source)
    return baseline
