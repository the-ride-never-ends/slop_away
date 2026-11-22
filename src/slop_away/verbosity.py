"""Check filler, hedges, budgets, and repeated sentences."""

import re
from pathlib import Path

from slop_away.config import Config
from slop_away.findings import Finding, make_finding
from slop_away.markdown import Document
from slop_away.text import split_sentences, word_matches

FILLER = re.compile(
    r"\bit[\s*_~]+is[\s*_~]+worth[\s*_~]+noting[\s*_~]+that\b"
    r"|\bin[\s*_~]+order[\s*_~]+to\b"
    r"|\bit[\s*_~]+is[\s*_~]+important[\s*_~]+to[\s*_~]+note[\s*_~]+that\b",
    re.IGNORECASE,
)
HEDGE = re.compile(
    r"\bmight[\s*_~]+possibly\b|\bit[\s*_~]+seems[\s*_~]+that\b"
    r"|\barguably\b",
    re.IGNORECASE,
)


def scan_verbosity(
    text: str,
    path: Path,
    config: Config,
    document: Document,
    seen: dict[str, Path],
) -> list[Finding]:
    """Check the verbosity rules.

    Args:
        text: The Markdown source.
        path: The source path.
        config: The document settings.
        document: The extracted Markdown text.
        seen: First paths for sentences from files checked in this run.

    Returns:
        The verbosity findings.
    """
    findings = []
    words = [
        (block.prose, match)
        for block in document.blocks
        for match in word_matches(block.prose.text)
    ]
    if (
        config.enabled("VRB003")
        and config.word_budget is not None
        and len(words) > config.word_budget
    ):
        projection, match = words[0]
        findings.append(
            make_finding(
                "VRB003",
                projection.offsets[match.start()],
                text,
                path,
                "\n".join(block.prose.text for block in document.blocks),
                f"Word count {len(words)} is above the budget "
                f"{config.word_budget}.",
                "Remove text until the document is within its word budget.",
            )
        )
    local: set[str] = set()
    for block in document.blocks:
        for sentence in split_sentences(block.prose):
            for code, pattern, message, hint in (
                (
                    "VRB001",
                    FILLER,
                    "Filler phrase in prose.",
                    "Remove the filler phrase.",
                ),
                (
                    "VRB002",
                    HEDGE,
                    "Hedge phrase in prose.",
                    "State the supported fact directly.",
                ),
            ):
                if config.enabled(code):
                    for match in pattern.finditer(sentence.text):
                        findings.append(
                            make_finding(
                                code,
                                sentence.offsets[match.start()],
                                text,
                                path,
                                sentence.text,
                                message,
                                hint,
                            )
                        )
            if len(word_matches(sentence.text)) < 8:
                continue
            normalized = " ".join(sentence.text.casefold().split())
            if config.enabled("VRB004") and normalized in local:
                findings.append(
                    make_finding(
                        "VRB004",
                        sentence.offsets[0],
                        text,
                        path,
                        sentence.text,
                        "Sentence is repeated in this document.",
                        "Remove the repeated sentence.",
                    )
                )
            local.add(normalized)
            if config.enabled("VRB005"):
                if normalized in seen and seen[normalized] != path:
                    findings.append(
                        make_finding(
                            "VRB005",
                            sentence.offsets[0],
                            text,
                            path,
                            sentence.text,
                            f"Sentence is also in "
                            f"{seen[normalized].as_posix()}.",
                            "Keep one copy of the sentence and use a link.",
                        )
                    )
                seen.setdefault(normalized, path)
    return findings
