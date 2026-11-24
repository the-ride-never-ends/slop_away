"""Test accuracy rates and their limits."""

import json
from pathlib import Path

import pytest

from tests.accuracy.scoring import compare_rates, measure_cases
from tests.accuracy.templates import templates


@pytest.fixture
def template_case():
    """GIVEN fixed labels WHEN measured THEN meet the recorded rates."""
    path = Path(__file__).parent / "accuracy/ratchet.json"
    policy = json.loads(path.read_text())["templates"]
    return templates(), policy, True


def test_template_ratchet(template_case):
    """GIVEN template labels WHEN measured THEN keep precision and recall."""
    cases, policy, expected = template_case
    actual = measure_cases(cases)
    passed = all(
        actual[rule][key] >= value["measured"][key]
        for rule, value in policy.items()
        for key in ("precision", "recall")
    )
    assert passed is expected


@pytest.fixture(params=["same", "higher", "ratchet", "minimum"])
def rate_case(request):
    """GIVEN measured rates WHEN checked THEN apply both rate limits."""
    actual = {"STE003": {"precision": 0.95, "recall": 0.9}}
    policy = {
        "STE003": {
            "minimum": {"precision": 0.9, "recall": 0.8},
            "measured": {"precision": 0.95, "recall": 0.9},
        }
    }
    expected = []
    if request.param == "higher":
        actual["STE003"]["precision"] = 0.99
    if request.param == "ratchet":
        actual["STE003"]["precision"] = 0.94
        expected = ["STE003 precision: expected 0.95; got 0.94."]
    if request.param == "minimum":
        policy["STE003"]["minimum"]["recall"] = 0.92
        expected = ["STE003 recall: expected 0.92; got 0.9."]
    return actual, policy, expected


def test_accuracy_limits(rate_case):
    """GIVEN rates WHEN compared THEN report every unmet limit."""
    actual, policy, expected = rate_case
    failures = compare_rates(actual, policy)
    assert failures == expected


@pytest.fixture(params=[None, -0.1, 1.1, True, float("nan")])
def missing_limit(request):
    """GIVEN an invalid owner limit WHEN checked THEN reject the policy."""
    actual = {"STE003": {"precision": 0.9, "recall": 0.8}}
    policy = {
        "STE003": {
            "minimum": {"precision": request.param},
            "measured": {"precision": 0.9},
        }
    }
    return actual, policy, ValueError


def test_owner_limit_required(missing_limit):
    """GIVEN no valid owner limit WHEN verified THEN fail fast."""
    actual, policy, expected = missing_limit
    with pytest.raises(expected) as error:
        compare_rates(actual, policy)
    assert type(error.value) is expected
