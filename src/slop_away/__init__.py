"""Check documentation and commit messages."""

from slop_away.checks import check_files, check_text
from slop_away.config import Config, ConfigError, load_config
from slop_away.findings import Finding
from slop_away.selection import select_files

__all__ = [
    "Config",
    "ConfigError",
    "Finding",
    "check_files",
    "check_text",
    "load_config",
    "select_files",
]
