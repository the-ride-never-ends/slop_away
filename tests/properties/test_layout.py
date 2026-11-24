"""Check that layout edits keep finding identities."""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from slop_away import Config, check_text
from tests.generation.documents import DOCUMENTS, transform


@pytest.fixture(scope="module", params=DOCUMENTS, ids=lambda item: item[0].name)
def layout_case(request):
    """GIVEN corpus text WHEN layout changes THEN keep its finding set."""
    path, logical = request.param
    source = path.read_text()
    config = Config()
    expected = {
        (item.code, item.fingerprint) for item in check_text(source, logical, config)
    }

    def prepare(operation, data):
        """GIVEN an edit WHEN checked THEN compare finding identities."""
        widths = (
            st.integers(min_value=30, max_value=100)
            if operation == "wrap"
            else st.sampled_from((30, 31, 32))
            if operation == "blanks"
            else st.just(30)
        )
        width = data.draw(widths)
        return transform(source, operation, width), logical, config, expected

    return prepare


@pytest.mark.parametrize("operation", ["wrap", "markers", "blanks", "sections"])
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(data=st.data())
def test_layout_identity(layout_case, operation, data):
    """GIVEN a layout edit WHEN checked THEN keep codes and fingerprints."""
    text, path, config, expected = layout_case(operation, data)
    findings = check_text(text, path, config)
    actual = {(item.code, item.fingerprint) for item in findings}
    assert actual == expected
