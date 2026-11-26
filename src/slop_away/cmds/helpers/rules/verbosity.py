"""Check filler, hedges, budgets, and repeated sentences."""

import re
from pathlib import Path

from slop_away.config import Config
from slop_away.utils.findings import Finding, make_finding
from slop_away.utils.markdown import Document
from slop_away.utils.text import split_sentences, word_matches

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
    *,
    text: str,
    path: Path,
    config: Config,
    doc: Document,
    seen: dict[str, Path],
) -> list[Finding]:
    """Check the verbosity rules.

    Args:
        text: The Markdown source.
        path: The source path.
        config: The document settings.
        doc: The extracted Markdown text.
        seen: First paths for sentences from files checked in this run.

    Returns:
        The verbosity findings.
    """
    findings = []
    words = [
        (block.prose, match)
        for block in doc.blocks
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
                code="VRB003",
                offset=projection.offsets[match.start()],
                text=text,
                path=path,
                context="\n".join(block.prose.text for block in doc.blocks),
                message=f"Word count {len(words)} is above the budget "
                f"{config.word_budget}.",
                hint="Remove text until the document is within its word budget.",
            )
        )
    local: set[str] = set()
    for block in doc.blocks:
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
                                code=code,
                                offset=sentence.offsets[match.start()],
                                text=text,
                                path=path,
                                context=sentence.text,
                                message=message,
                                hint=hint,
                            )
                        )
            if len(word_matches(sentence.text)) < 8:
                continue
            normalized = " ".join(sentence.text.casefold().split())
            if config.enabled("VRB004") and normalized in local:
                findings.append(
                    make_finding(
                        code="VRB004",
                        offset=sentence.offsets[0],
                        text=text,
                        path=path,
                        context=sentence.text,
                        message="Sentence is repeated in this document.",
                        hint="Remove the repeated sentence.",
                    )
                )
            local.add(normalized)
            if config.enabled("VRB005"):
                if normalized in seen and seen[normalized] != path:
                    findings.append(
                        make_finding(
                            code="VRB005",
                            offset=sentence.offsets[0],
                            text=text,
                            path=path,
                            context=sentence.text,
                            message=f"Sentence is also in "
                            f"{seen[normalized].as_posix()}.",
                            hint="Keep one copy of the sentence and use a link.",
                        )
                    )
                seen.setdefault(normalized, path)
    return findings
