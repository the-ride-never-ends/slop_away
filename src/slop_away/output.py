"""Format finding reports."""

import json
from collections.abc import Sequence
from dataclasses import asdict

from slop_away.findings import Finding


def _escape(value: str, property: bool = False) -> str:
    """Escape annotation text.

    Args:
        value: The command data or property value.
        property: Escape property separators as well as command data.

    Returns:
        The escaped value.
    """
    value = value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    if property:
        value = value.replace(":", "%3A").replace(",", "%2C")
    return value


def render_findings(
    findings: Sequence[Finding], output_format: str = "text"
) -> str:
    """Format a finding report.

    Args:
        findings: The findings in report order.
        output_format: The text, agent, json, or github output format.

    Returns:
        The report with a final line ending, or empty human-readable output.

    Raises:
        ValueError: The output format is unknown.
    """
    if output_format not in {"text", "agent", "json", "github"}:
        raise ValueError(f"Unknown output format {output_format!r}.")
    if output_format == "json":
        records = [
            {**asdict(finding), "path": finding.path.as_posix()}
            for finding in findings
        ]
        return json.dumps(records, ensure_ascii=False, indent=2) + "\n"
    lines = []
    for finding in findings:
        path = finding.path.as_posix()
        location = f"{path}:{finding.line}:{finding.column}"
        if output_format == "text":
            lines.append(f"{location}: {finding.code} {finding.message}")
        elif output_format == "agent":
            lines.append(
                f"{finding.code} {location} {finding.message} "
                f"Fix: {finding.hint}"
            )
        else:
            lines.append(
                f"::error file={_escape(path, True)},line={finding.line},"
                f"col={finding.column},title={_escape(finding.code, True)}"
                f"::{_escape(finding.message)}"
            )
    return "\n".join(lines) + ("\n" if lines else "")
