"""Check documentation and commit messages."""

from slop_away.checks import check_files, check_text, fix_files
from slop_away.config import Config, ConfigError, load_config
from slop_away.findings import Finding
from slop_away.fixes import apply_fixes
from slop_away.package_types import PackageError
from slop_away.packages import sync_packages
from slop_away.selection import select_files

__all__ = [
    "Config",
    "ConfigError",
    "Finding",
    "PackageError",
    "apply_fixes",
    "check_files",
    "check_text",
    "fix_files",
    "load_config",
    "select_files",
    "sync_packages",
]
