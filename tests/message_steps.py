"""Supply commit-message feature steps."""

from pytest_bdd import parsers, when

from slop_away import check_message


@when(
    parsers.parse('check_message runs on the message "{text}"'),
    target_fixture="findings",
)
def message_text(config, text):
    """GIVEN a message WHEN checked THEN return its findings."""
    return check_message(text, config)


@when("check_message runs on the message:", target_fixture="findings")
def message_document(config, docstring):
    """GIVEN a message block WHEN checked THEN return its findings."""
    return check_message(docstring, config)


@when(
    parsers.parse(
        "check_message runs on a message with a subject of "
        "{count:d} characters"
    ),
    target_fixture="findings",
)
def subject_length(config, count):
    """GIVEN a long subject WHEN checked THEN report its length."""
    return check_message("x" * count, config)


@when(
    parsers.parse(
        "check_message runs on a message with a body of {count:d} words"
    ),
    target_fixture="findings",
)
def body_length(config, count):
    """GIVEN a long body WHEN checked THEN report its word count."""
    return check_message(
        "Add the parser\n\n" + " ".join(["word"] * count), config
    )
