"""Prepare the pinned independent parser models."""

import hashlib
import json
import sys
from pathlib import Path

POLICY = json.loads(Path(__file__).with_name("models.json").read_text())
DIRECTORY = Path(sys.prefix) / "share/stanza"


def verify_models():
    """Check the independent parser model files.

    Raises:
        OSError: A model file is absent.
        ValueError: A model does not match its pinned hash.
    """
    for item in POLICY["files"]:
        path = DIRECTORY / item["path"]
        actual = hashlib.md5(path.read_bytes(), usedforsecurity=False).hexdigest()
        if actual != item["md5"]:
            raise ValueError(f"{path}: the model hash does not match.")


def main():
    """Download the independent parser models."""
    import stanza

    stanza.download(
        "en",
        model_dir=str(DIRECTORY),
        package=None,
        processors=POLICY["processors"],
        resources_version=POLICY["resources"],
        verbose=False,
    )
    verify_models()


if __name__ == "__main__":
    main()
