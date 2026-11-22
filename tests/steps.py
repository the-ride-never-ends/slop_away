"""Supply feature steps for the public API and commands."""

import ast
import os
import re
import shlex
from pathlib import Path
from subprocess import CompletedProcess

from pytest_bdd import given, parsers, then, when

from slop_away import (
    Config,
    ConfigError,
    Finding,
    check_files,
    check_text,
    load_config,
    select_files,
)
from tests.harnesses import CliHarness, GitHarness


@given(parsers.parse('a file "{path}" containing:'))
def write_file(tmp_path: Path, path: str, docstring: str):
    """GIVEN source text WHEN a file is needed THEN create the file."""
    target = tmp_path / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(docstring, encoding="utf-8")


@given("these files exist:")
def write_files(tmp_path: Path, datatable: list[list[str]]):
    """GIVEN paths WHEN a project is needed THEN create the files."""
    for (path,) in datatable[1:]:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("", encoding="utf-8")


@given("the default config", target_fixture="config")
def default_config(tmp_path: Path):
    """GIVEN no settings WHEN a check runs THEN use default settings."""
    return Config(root=tmp_path)


@given("the config is loaded from the project root", target_fixture="config")
def project_config(tmp_path: Path):
    """GIVEN project settings WHEN a check runs THEN use those settings."""
    return load_config(tmp_path)


@when("load_config runs on the project root", target_fixture="loaded")
def read_config(tmp_path: Path):
    """GIVEN settings WHEN config loads THEN return its result or error."""
    try:
        return load_config(tmp_path)
    except ConfigError as error:
        return error


@then(parsers.parse("config.select equals {value}"))
def check_select(loaded: Config, value: str):
    """GIVEN settings WHEN rules are selected THEN retain that list."""
    expected = ast.literal_eval(value)
    actual = loaded.select
    assert actual == expected, f"Expected select {expected}; got {actual}."


@then("load_config raises ConfigError")
def config_error(loaded):
    """GIVEN invalid settings WHEN config loads THEN raise ConfigError."""
    expected = ConfigError
    actual = type(loaded)
    assert actual is expected, f"Expected {expected}; got {actual}."


@then(parsers.parse('the error message contains "{key}"'))
def error_key(loaded: ConfigError, key: str):
    """GIVEN a config error WHEN reported THEN name the invalid setting."""
    actual = str(loaded)
    assert key in actual, f"Expected error to name {key!r}; got {actual!r}."


@then("the loaded config equals the default config")
def config_default(loaded: Config):
    """GIVEN no tool section WHEN config loads THEN use default settings."""
    expected = Config()
    assert loaded == expected


@when(
    parsers.parse('check_text runs on "{path}" with the text:'),
    target_fixture="findings",
)
def check_document(config: Config, path: str, docstring: str):
    """GIVEN Markdown WHEN checked THEN return its findings."""
    return check_text(docstring, path, config)


@when(
    parsers.parse('check_text runs on "{path}" with the text "{text}"'),
    target_fixture="findings",
)
def check_string(config: Config, path: str, text: str):
    """GIVEN text WHEN checked THEN return its findings."""
    return check_text(text, path, config)


@when(
    parsers.parse(
        'check_text runs on "{path}" with text containing '
        "the character U+{codepoint}"
    ),
    target_fixture="findings",
)
def check_character(config: Config, path: str, codepoint: str):
    """GIVEN a hidden character WHEN checked THEN return its findings."""
    return check_text(chr(int(codepoint, 16)), path, config)


@when(
    parsers.parse(
        'check_text runs on "{path}" with a text of {count:d} words'
    ),
    target_fixture="findings",
)
def check_words(config: Config, path: str, count: int):
    """GIVEN a word count WHEN checked THEN return the findings."""
    return check_text(" ".join(["word"] * count), path, config)


@when(parsers.parse("check_files runs on {paths}"), target_fixture="findings")
def check_paths(config: Config, paths: str):
    """GIVEN document paths WHEN checked THEN return all findings."""
    return check_files(ast.literal_eval(paths), config)


@then(parsers.parse('check_text returns a finding with code "{code}"'))
@then(parsers.parse('check_files returns a finding with code "{code}"'))
def has_finding(findings: list[Finding], code: str):
    """GIVEN findings WHEN a rule matches THEN include its code."""
    actual = [finding.code for finding in findings]
    assert code in actual, f"Expected code {code}; got {actual}."


@then(parsers.parse('check_text returns no finding with code "{code}"'))
def lacks_finding(findings: list[Finding], code: str):
    """GIVEN findings WHEN a rule does not match THEN omit its code."""
    actual = [finding.code for finding in findings]
    assert code not in actual, f"Expected no code {code}; got {actual}."


@then("check_text returns no findings")
def no_findings(findings: list[Finding]):
    """GIVEN valid text WHEN checked THEN return no findings."""
    expected: list[Finding] = []
    assert findings == expected


@when(parsers.parse("select_files runs on {paths}"), target_fixture="selected")
def choose_files(config: Config, paths: str):
    """GIVEN project paths WHEN selected THEN return Markdown paths."""
    return select_files(ast.literal_eval(paths), config)


@then(parsers.parse('the result contains "{path}"'))
def has_path(selected: list[Path], tmp_path: Path, path: str):
    """GIVEN selected paths WHEN a file applies THEN include its path."""
    expected = tmp_path / path
    assert expected in selected


@then(parsers.parse('the result does not contain "{path}"'))
def lacks_path(selected: list[Path], tmp_path: Path, path: str):
    """GIVEN selected paths WHEN a file is excluded THEN omit its path."""
    excluded = tmp_path / path
    assert excluded not in selected


@when(parsers.parse('I run "{command}"'), target_fixture="result")
def run_command(cli: CliHarness, command: str) -> CompletedProcess[str]:
    """GIVEN a command WHEN it runs THEN collect its result."""
    return cli.run(shlex.split(command))


@then(parsers.parse("the exit code is {expected:d}"))
def check_exit(result: CompletedProcess[str], expected: int):
    """GIVEN a result WHEN the command ends THEN check its exit code."""
    actual = result.returncode
    assert actual == expected, f"Expected exit code {expected}; got {actual}."


@then(parsers.parse("the exit code is not {excluded:d}"))
def exclude_exit(result: CompletedProcess[str], excluded: int):
    """GIVEN an invalid document WHEN committed THEN block the commit."""
    actual = result.returncode
    assert actual != excluded


@then(parsers.parse('stdout matches "{pattern}"'))
def check_stdout(result: CompletedProcess[str], pattern: str):
    """GIVEN output WHEN a pattern is specified THEN check the output."""
    actual = result.stdout
    assert re.fullmatch(pattern, actual.rstrip("\n")), (
        f"Expected stdout to match {pattern!r}; got {actual!r}."
    )


@then(parsers.re(r"(?P<channel>stdout|stderr) is empty"))
def empty_output(result: CompletedProcess[str], channel: str):
    """GIVEN a result WHEN no output is specified THEN check the channel."""
    expected = ""
    actual = getattr(result, channel)
    assert actual == expected, f"Expected empty {channel}; got {actual!r}."


@then(parsers.re(r'(?P<channel>stdout|stderr) contains "(?P<text>.*)"'))
def contains_output(result: CompletedProcess[str], channel: str, text: str):
    """GIVEN a result WHEN text is specified THEN check the channel."""
    actual = getattr(result, channel)
    assert text in actual, f"Expected {text!r} in {channel}; got {actual!r}."


@given(
    "a git repository with the slop_away pre-commit hooks installed",
    target_fixture="cli",
)
def git_project(tmp_path: Path):
    """GIVEN a test project WHEN Git is needed THEN install its hook."""
    environment = {
        "PRE_COMMIT_HOME": str(tmp_path / "cache"),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    harness = GitHarness(tmp_path, environment)
    harness.install(
        Path(__file__).resolve().parents[1] / ".pre-commit-hooks.yaml"
    )
    return harness


@given(parsers.parse('a staged file "{path}" containing:'))
def staged_file(cli: GitHarness, path: str, docstring: str):
    """GIVEN a document WHEN a commit is needed THEN stage the document."""
    cli.stage(path, docstring)
