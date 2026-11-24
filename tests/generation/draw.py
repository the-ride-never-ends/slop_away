"""Draw external documents from a fixed candidate list."""

import argparse
import hashlib
import json
import random
import re
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

from langdetect import DetectorFactory, detect_langs  # type: ignore[import-untyped]
from langdetect.lang_detect_exception import (  # type: ignore[import-untyped]
    ErrorCode,
    LangDetectException,
)
from markdown_it import MarkdownIt

from slop_away.markdown import parse_document
from slop_away.text import word_matches

ROOT = Path(__file__).resolve().parents[1] / "corpus/external"
DetectorFactory.seed = 0
QUOTAS = {
    "readme": (3, 3),
    "contributor": (2, 2),
    "changelog": (2, 2),
    "roadmap": (2, 2),
    "design": (2, 2),
    "agent": (0, 4),
    "tutorial": (2, 2),
}


def measure(text):
    """Measure document size and excluded lines.

    Args:
        text: The source document.

    Returns:
        Its prose word count, excluded line count, and total line count.
    """
    lines = text.splitlines()
    excluded = set()
    for token in MarkdownIt("gfm-like").parse(text):
        if token.type in {"fence", "code_block", "table_open"} and token.map:
            excluded.update(range(*token.map))
    excluded.update(
        index
        for index, line in enumerate(lines)
        if re.fullmatch(r"\s*<?https?://\S+>?\s*", line)
    )
    return len(word_matches(parse_document(text).prose.text)), len(excluded), len(lines)


def identify(files):
    """Identify a permitted license in source files.

    Args:
        files: The root license files at the source commit.

    Returns:
        The license identifier, or None for other terms.
    """
    for file in files:
        text = file["text"]
        if "Permission is hereby granted, free of charge" in text:
            return "MIT"
        if "Apache License" in text and "Version 2.0" in text:
            return "Apache-2.0"
        if "Redistribution and use in source and binary forms" in text:
            return "BSD-3-Clause" if "Neither the name" in text else "BSD-2-Clause"
    return None


def english(text):
    """Check whether the document contains English prose.

    Args:
        text: The source document.

    Returns:
        True if English has a probability of at least 0.95.
    """
    prose = " ".join(parse_document(text).prose.text.split())
    try:
        languages = detect_langs(prose)
    except LangDetectException as error:
        if error.code == ErrorCode.CantDetectError:
            return False
        raise
    return languages[0].lang == "en" and languages[0].prob >= 0.95


def download(candidate):
    """Read a pinned source document.

    Args:
        candidate: The source repository, commit, and path.

    Returns:
        The source bytes.
    """
    path = quote(candidate["path"], safe="/")
    url = (
        f"https://raw.githubusercontent.com/{candidate['repo']}/"
        f"{candidate['commit']}/{path}"
    )
    for attempt in range(3):
        try:
            with urlopen(url, timeout=30) as response:
                return response.read()
        except HTTPError as error:
            if error.code != 503 or attempt == 2:
                raise
            time.sleep(attempt + 1)


def draw(seed, reader=download):
    """Draw the required document groups.

    Args:
        seed: The first draw seed.
        reader: The source reader.

    Returns:
        The selected documents and the record of each draw.

    Raises:
        ValueError: The seed or candidate list is invalid.
        RuntimeError: A group has too few eligible documents.
    """
    if type(seed) is not int or seed < 0:
        raise ValueError("Expected a nonnegative integer seed.")
    catalog = json.loads((ROOT / "candidates.json").read_text())
    licenses = {
        item["key"]: item["files"]
        for item in json.loads((ROOT / "licenses.json").read_text())
    }
    selected, attempts = [], []
    for kind, quotas in QUOTAS.items():
        for era, count in zip(("old", "new"), quotas, strict=True):
            pool = sorted(
                (
                    item
                    for item in catalog["candidates"]
                    if item["type"] == kind and item["era"] == era
                ),
                key=lambda item: (item["repo"], item["commit"], item["path"]),
            )
            accepted = 0
            while accepted < count:
                if not pool:
                    raise RuntimeError(f"Too few eligible {era} {kind} documents.")
                index = random.Random(seed).randrange(len(pool))
                item = pool.pop(index)
                files = licenses.get(f"{item['repo']}@{item['commit']}", [])
                license_id = identify(files)
                reason = None
                source = None
                if item["stars"] < 20 or not license_id:
                    reason = "license or stars"
                elif era == "new" and item["date"] < "2023":
                    reason = "date"
                else:
                    source = reader(item)
                    words, excluded, lines = measure(source.decode("utf-8"))
                    if words < 150:
                        reason = "fewer than 150 prose words"
                    elif excluded * 2 > lines:
                        reason = "excluded lines exceed half"
                    elif not english(source.decode("utf-8")):
                        reason = "non-English prose"
                attempts.append(
                    {
                        "seed": seed,
                        "repo": item["repo"],
                        "commit": item["commit"],
                        "path": item["path"],
                        "type": kind,
                        "era": era,
                        "rejection": reason,
                    }
                )
                seed += 1
                if reason:
                    continue
                filename = f"{kind}-{era}-{accepted + 1}.md"
                record = {
                    **item,
                    "file": filename,
                    "license": license_id,
                    "sha256": hashlib.sha256(source).hexdigest(),
                    "words": words,
                    "excluded_lines": excluded,
                    "lines": lines,
                    "seed": seed - 1,
                }
                selected.append((record, source, files))
                accepted += 1
    return selected, attempts


def main():
    """Write the selected documents and their source records."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    arguments = parser.parse_args()
    selected, attempts = draw(arguments.seed)
    for item, source, files in selected:
        (ROOT / item["file"]).write_bytes(source)
        directory = ROOT / "licenses" / item["file"].removesuffix(".md")
        directory.mkdir(parents=True, exist_ok=True)
        for prior in directory.iterdir():
            if prior.is_file():
                prior.unlink()
        for file in files:
            (directory / Path(file["path"]).name).write_text(file["text"])
    manifest = {
        "seed": arguments.seed,
        "documents": [item for item, _source, _files in selected],
        "attempts": attempts,
    }
    (ROOT / "sources.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
