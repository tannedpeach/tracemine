"""Existing token-value contract; shlex is the independent reference oracle."""
import shlex
import pytest
from hypothesis import given, settings, strategies as st
from app import create_app
from query import tokenize


@pytest.mark.parametrize("query, expected", [
    ('status:open owner:"Ada Lovelace"', ["status:open", "owner:Ada Lovelace"]),
    ('a\\ b "c d" \'e f\'', ["a b", "c d", "e f"]),
    ('"" \'\' foo#bar', ["", "", "foo#bar"]),
    ("tabs\tand\nlines", ["tabs", "and", "lines"]),
])
def test_examples(query, expected):
    assert tokenize(query) == expected


@given(st.text(alphabet="abcXYZ012 :_-/.$#'\"\\\t\r\n\u00a0é", max_size=100))
@settings(print_blob=True)
def test_token_values_match_posix_shlex(query):
    try:
        expected = shlex.split(query, comments=False, posix=True)
    except ValueError:
        with pytest.raises(ValueError):
            tokenize(query)
    else:
        assert tokenize(query) == expected


def test_endpoint():
    client = create_app().test_client()
    assert client.post("/parse", json={"query": 'owner:"Ada Lovelace"'}).json == {
        "tokens": ["owner:Ada Lovelace"]
    }
    assert client.post("/parse", json={"query": '"unclosed'}).status_code == 400
    assert client.post("/parse", json={"query": None}).status_code == 400
