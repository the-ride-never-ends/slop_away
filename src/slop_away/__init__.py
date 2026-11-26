"""Check documentation and commit messages."""

from slop_away.cmds.baseline import Baseline, load_baseline, write_baseline
from slop_away.cmds.checks import check_files, check_text, fix_files
from slop_away.cmds.guard import guard_command
from slop_away.cmds.helpers.fixes import apply_fixes
from slop_away.cmds.helpers.packages import sync_packages
from slop_away.cmds.helpers.rules.readability import SectionGrade, grade_sections
from slop_away.cmds.initialize import init_project
from slop_away.cmds.messages import check_message
from slop_away.cmds.render import render_findings
from slop_away.config import Config, load_config
from slop_away.utils.exceptions import ConfigError, PackageError
from slop_away.utils.findings import Finding
from slop_away.utils.selection import select_files

__all__ = [
    "Baseline",
    "Config",
    "ConfigError",
    "Finding",
    "PackageError",
    "SectionGrade",
    "apply_fixes",
    "check_files",
    "check_message",
    "check_text",
    "fix_files",
    "grade_sections",
    "guard_command",
    "init_project",
    "load_baseline",
    "load_config",
    "render_findings",
    "select_files",
    "sync_packages",
    "write_baseline",
]
