"""Supply baseline and report feature steps."""

import json
import shlex

from pytest_bdd import given, parsers, then

from slop_away import Baseline, check_text


@given(parsers.parse('I have run "{command}"'))
def prior_command(cli, command):
    """GIVEN a prior command WHEN checking THEN use its saved result."""
    cli.run(shlex.split(command)).check_returncode()


@given(parsers.parse('the line "{line}" is appended to "{path}"'))
def append_line(tmp_path, path, line):
    """GIVEN a document WHEN new text is needed THEN append the line."""
    with (tmp_path / path).open("a", encoding="utf-8") as stream:
        stream.write("\n" + line + "\n")


@given(
    parsers.parse(
        'a baseline built from the findings of check_text on "{path}" '
        'with the text "{text}"'
    ),
    target_fixture="baseline",
)
def built_baseline(config, path, text):
    """GIVEN findings WHEN later text is checked THEN keep their baseline."""
    return Baseline.build(check_text(text, path, config))


@then(parsers.parse('the file "{path}" exists'))
def stored_file(tmp_path, path):
    """GIVEN a command WHEN a file is written THEN keep the file."""
    assert (tmp_path / path).is_file()


@then(
    parsers.parse(
        "baseline.matches returns {expected} "
        'for the finding with code "{code}"'
    )
)
def matched_baseline(baseline, findings, expected, code):
    """GIVEN a baseline WHEN a finding is compared THEN match its context."""
    finding = next(finding for finding in findings if finding.code == code)
    actual = baseline.matches(finding)
    expected = expected == "True"
    assert actual is expected


@then("stdout parses as a JSON array")
def json_array(result):
    """GIVEN JSON output WHEN parsed THEN return an array of findings."""
    actual = json.loads(result.stdout)
    assert isinstance(actual, list), f"Expected a JSON array; got {actual!r}."


@then(parsers.parse('the first element has "{key}" equal to "{value}"'))
def json_field(result, key, value):
    """GIVEN JSON findings WHEN inspected THEN include the rule code."""
    actual = json.loads(result.stdout)[0][key]
    assert actual == value, f"Expected {key} {value!r}; got {actual!r}."


@then(parsers.parse('stdout starts with "{prefix}"'))
def output_prefix(result, prefix):
    """GIVEN annotations WHEN reported THEN use the expected prefix."""
    actual = result.stdout
    assert actual.startswith(prefix)
