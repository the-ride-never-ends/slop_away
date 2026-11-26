"""Replace text files without partial file contents."""

import os
import tempfile
from pathlib import Path


def write_text(*, path: Path, text: str, mode: int | None = None) -> None:
    """Replace a text file.

    Args:
        path: The destination file.
        text: The new UTF-8 source text.
        mode: New permissions, or None to retain existing permissions.

    Raises:
        OSError: The file cannot be written or replaced.
    """
    if mode is None and path.exists():
        mode = path.stat().st_mode
    temp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            delete=False,
        ) as f:
            temp = Path(f.name)
            f.write(text)
        if mode is not None:
            temp.chmod(mode)
        os.replace(temp, path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
