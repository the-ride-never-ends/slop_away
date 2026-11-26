"""Supply corpus checks and comparison reports."""

from dataclasses import dataclass
from pathlib import Path

from slop_away import Config, check_files

CORPUS_ROOT = Path(__file__).parent / "corpus"
REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class CorpusHarness:
    """GIVEN corpus files WHEN checked THEN report code changes by path."""

    root: Path = CORPUS_ROOT

    def check(self, group: str) -> dict[str, list[str]]:
        """GIVEN a corpus group WHEN checked THEN collect its native codes."""
        result = {}
        config = Config(root=self.root)
        for path in sorted((self.root / group).rglob("*.md")):
            relative = path.relative_to(self.root).as_posix()
            result[relative] = sorted(
                {item.code for item in check_files(paths=[path], config=config)}
            )
        if not result:
            raise ValueError(f"Empty corpus group {group!r}.")
        return result

    def compare(
        self, actual: dict[str, list[str]], expected: dict[str, list[str]]
    ) -> str:
        """GIVEN expected codes WHEN compared THEN name each changed path."""
        report = []
        for path in sorted(actual.keys() | expected.keys()):
            if path not in actual or path not in expected:
                report.append(f"{path}: missing document or expectation.")
                continue
            gained = sorted(set(actual[path]) - set(expected[path]))
            lost = sorted(set(expected[path]) - set(actual[path]))
            if gained or lost:
                report.append(f"{path}: gained {gained}; lost {lost}.")
        return "\n".join(report)
