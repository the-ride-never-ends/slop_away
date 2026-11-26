"""Measure rule precision and recall."""

from slop_away import Config, check_message, check_text
from tests.accuracy.templates import RULES


def predict(rule, text):
    """Check one labeled sentence.

    Args:
        rule: The rule to measure.
        text: The source text.

    Returns:
        True if the rule reports a finding.

    Raises:
        ValueError: The rule is unknown.
    """
    if rule not in RULES:
        raise ValueError(f"Unknown accuracy rule {rule!r}.")
    code = "STE001" if rule == "procedure" else rule
    config = Config(select=[code])
    if rule == "MSG002":
        findings = check_message(text=text, config=config)
    else:
        findings = check_text(text=text, path="sample.md", config=config)
    return bool(findings)


def measure_cases(cases):
    """Measure a complete labeled set.

    Args:
        cases: Rule, text, and expected finding records.

    Returns:
        Counts, precision, and recall for each rule.

    Raises:
        ValueError: A rule lacks either label class.
    """
    counts = {rule: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for rule in RULES}
    for rule, text, expected in cases:
        actual = predict(rule, text)
        key = ("tp" if expected else "fp") if actual else ("fn" if expected else "tn")
        counts[rule][key] += 1
    for rule, values in counts.items():
        tp, fp, fn, tn = (values[key] for key in ("tp", "fp", "fn", "tn"))
        if not tp + fn or not fp + tn:
            raise ValueError(f"{rule}: both label classes are required.")
        values["precision"] = tp / (tp + fp) if tp + fp else 0.0
        values["recall"] = tp / (tp + fn)
    return counts


def compare_rates(actual, policy):
    """Compare measured rates with their limits.

    Args:
        actual: The measured counts and rates.
        policy: The last rates and owner limits.

    Returns:
        Each unmet limit.

    Raises:
        ValueError: An owner limit is absent or invalid.
    """
    failures = []
    if policy is None:
        raise ValueError("The owner has not set the limits for this suite.")
    if set(actual) != set(policy):
        raise ValueError("Accuracy rules do not match the policy.")
    for rule, values in actual.items():
        for metric in ("precision", "recall"):
            minimum = policy[rule]["minimum"][metric]
            if type(minimum) not in {float, int} or not 0 <= minimum <= 1:
                raise ValueError(f"{rule}: the owner must set {metric}.")
            limit = max(minimum, policy[rule]["measured"][metric])
            if values[metric] < limit:
                failures.append(
                    f"{rule} {metric}: expected {limit}; got {values[metric]}."
                )
    return failures
