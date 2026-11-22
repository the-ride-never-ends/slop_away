"""Replace text files without partial file contents."""

import os
import tempfile
from pathlib import Path


def write_text(path: Path, text: str) -> None:
    """Replace a text file.

    Args:
        path: The destination file.
        text: The new UTF-8 source text.

    Raises:
        OSError: The file cannot be written or replaced.
    """
    mode = path.stat().st_mode if path.exists() else None
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        if mode is not None:
            temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
