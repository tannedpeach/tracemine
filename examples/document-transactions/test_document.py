from copy import deepcopy

import pytest

from document import edit


def test_sequential_copy_append_and_list_removal():
    source = {"a": [{"tags": [1]}, {"tags": [2]}], "b": None}
    result = edit(
        source,
        [
            {"op": "copy", "from": ["a", 0], "path": ["b"]},
            {"op": "append", "path": ["a", 0, "tags"], "value": 3},
            {"op": "remove", "path": ["a", 0]},
            {"op": "test", "path": ["a", 0, "tags"], "value": [2]},
        ],
    )
    assert result == {"a": [{"tags": [2]}], "b": {"tags": [1]}}
    assert source == {"a": [{"tags": [1]}, {"tags": [2]}], "b": None}


@pytest.mark.parametrize(
    "bad",
    [
        {"op": "test", "path": ["a"], "value": "wrong"},
        {"op": "set", "path": ["missing", "x"], "value": 1},
        {"op": "remove", "path": []},
        {"op": "append", "path": ["a"], "value": 1},
    ],
)
def test_failure_does_not_mutate_inputs(bad):
    source = {"a": {"nested": [1]}, "untouched": [2]}
    value = {"nested": [3]}
    operations = [{"op": "set", "path": ["a"], "value": value}, bad]
    before = deepcopy((source, operations))
    with pytest.raises((ValueError, KeyError, AttributeError)):
        edit(source, operations)
    assert (source, operations) == before


def test_success_has_no_mutable_alias_to_source_or_operations():
    source = {"a": [1], "untouched": {"x": [2]}}
    operations = [{"op": "set", "path": ["a"], "value": [3]}]
    result = edit(source, operations)
    result["untouched"]["x"].append(4)
    result["a"].append(5)
    assert source == {"a": [1], "untouched": {"x": [2]}}
    assert operations[0]["value"] == [3]


def test_root_replacement_and_copy_are_sequential():
    source = {"x": [1]}
    result = edit(
        source,
        [
            {"op": "copy", "from": ["x"], "path": []},
            {"op": "append", "path": [], "value": {"a": 2}},
            {"op": "set", "path": [0], "value": 3},
        ],
    )
    assert result == [3, {"a": 2}]
    assert source == {"x": [1]}


def test_empty_batch_returns_independent_tree():
    source = {"a": [1]}
    result = edit(source, [])
    result["a"].append(2)
    assert source == {"a": [1]}
