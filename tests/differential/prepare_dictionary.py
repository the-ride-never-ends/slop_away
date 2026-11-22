"""Prepare equal pronunciation data for independent scoring tests."""

import sys
from importlib.metadata import version
from pathlib import Path

import cmudict


def prepare_dictionary(root: Path) -> None:
    """GIVEN installed CMU data WHEN compared THEN use one data edition."""
    directory = root / "share/nltk_data/corpora/cmudict"
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "cmudict").open("w", encoding="utf-8") as stream:
        for word, variants in sorted(cmudict.dict().items()):
            for number, phones in enumerate(variants, 1):
                stream.write(f"{word.upper()} {number} {' '.join(phones)}\n")
    (directory / "edition.txt").write_text(
        version("cmudict"), encoding="utf-8"
    )


if __name__ == "__main__":
    prepare_dictionary(Path(sys.argv[1]))
