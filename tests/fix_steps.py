"""Supply fix feature steps."""

from pytest_bdd import parsers, then, when

from slop_away import apply_fixes, check_text


@when(
    parsers.parse(
        'apply_fixes runs on "{path}" with the text "{text}" and unsafe {unsafe}'
    ),
    target_fixture="fixed",
)
def fix_document(config, path, text, unsafe):
    """GIVEN source text WHEN fixed THEN return the changed source."""
    return apply_fixes(text=text, path=path, config=config, unsafe=unsafe == "True")


@then(parsers.parse('apply_fixes returns "{expected}"'))
def fixed_text(fixed, expected):
    """GIVEN a fix result WHEN reported THEN return the expected text."""
    assert fixed == expected


@when(
    parsers.parse('check_text runs on "{path}" with the fixed text'),
    target_fixture="findings",
)
def check_fixed(config, path, fixed):
    """GIVEN fixed source WHEN checked THEN report remaining findings."""
    return check_text(fixed, path, config)


@when("apply_fixes runs again on its own result", target_fixture="second")
def repeat_fix(config, fixed):
    """GIVEN fixed text WHEN fixed again THEN return the second result."""
    return apply_fixes(text=fixed, path="docs/guide.md", config=config)


@then("the second result equals the first result")
def unchanged_fix(fixed, second):
    """GIVEN two fix passes WHEN compared THEN keep the same source."""
    assert second == fixed


@then(parsers.parse('the file "{path}" contains "{text}"'))
def saved_fix(tmp_path, path, text):
    """GIVEN a file fix WHEN complete THEN write the changed text."""
    actual = (tmp_path / path).read_text(encoding="utf-8")
    assert text in actual
