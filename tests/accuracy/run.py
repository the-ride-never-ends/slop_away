"""Run a labeled accuracy comparison."""

import argparse
import hashlib
import json
from pathlib import Path

from tests.accuracy.scoring import compare_rates, measure_cases
from tests.accuracy.templates import templates

ROOT = Path(__file__).parent


def main():
    """Write an accuracy report and check its limits when requested."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("templates", "external"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    arguments = parser.parse_args()
    if arguments.suite == "external":
        from tests.accuracy.reference import external_cases

        cases, sources = external_cases()
    else:
        cases, sources = templates(), []
    rates = measure_cases(cases)
    report = {
        "suite": arguments.suite,
        "cases": len(cases),
        "rates": rates,
        "labels_sha256": hashlib.sha256(json.dumps(cases).encode()).hexdigest(),
        "sources": sources,
    }
    arguments.output.write_text(json.dumps(report, indent=2) + "\n")
    if arguments.verify:
        policy = json.loads((ROOT / "ratchet.json").read_text())[arguments.suite]
        failures = compare_rates(rates, policy)
        if failures:
            raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
