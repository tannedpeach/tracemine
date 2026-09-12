from copy import deepcopy

import pytest

from store import Conflict, Store


def put(key, expected, value):
    return {"kind": "put", "key": key, "expected": expected, "value": value}


def delete(key, expected):
    return {"kind": "delete", "key": key, "expected": expected}


def test_sequential_versions_delete_recreate_and_alias_isolation():
    store = Store({"a": {"version": 3, "value": {"tags": ["old"]}}})
    store.read("a")
    body = {"tags": ["new"]}
    results = store.apply([put("a", 3, body), delete("a", 4), put("a", 0, body)])
    assert [item["version"] if item else None for item in results] == [4, None, 1]
    body["tags"].append("source")
    results[-1]["value"]["tags"].append("result")
    read = store.read("a")
    read["value"]["tags"].append("reader")
    assert store.read("a") == {"version": 1, "value": {"tags": ["new"]}}


@pytest.mark.parametrize("warm", [False, True])
@pytest.mark.parametrize("fail_at", range(5))
def test_staging_failure_restores_records_and_exact_cache_state(warm, fail_at):
    store = Store({"a": {"version": 2, "value": [1]}, "untouched": {"version": 1, "value": [9]}})
    if warm:
        store.read("a")
    store.read("untouched")
    before = deepcopy((store.records, store.cache))
    operations = [
        put("a", 2, [2]),
        put("a", 3, [3]),
        delete("a", 4),
        put("a", 0, [4]),
        put("b", 0, [5]),
    ]
    calls = []

    def persist(key, record):
        calls.append(key)
        # Callbacks can observe a read; rollback includes cache fills during the batch.
        store.read("untouched")
        if len(calls) - 1 == fail_at:
            raise OSError("staging rejected")

    with pytest.raises(OSError):
        store.apply(operations, persist)
    assert (store.records, store.cache) == before
    assert len(calls) == fail_at + 1


@pytest.mark.parametrize("warm", [False, True])
def test_late_conflict_and_invalid_operation_roll_back(warm):
    store = Store({"a": {"version": 1, "value": {"nested": [1]}}})
    if warm:
        store.read("a")
    before = deepcopy((store.records, store.cache))
    with pytest.raises(Conflict):
        store.apply([put("b", 0, []), put("a", 1, [2]), put("a", 1, [3])])
    assert (store.records, store.cache) == before
    with pytest.raises(ValueError):
        store.apply([delete("a", 1), {"key": "b", "expected": 0, "kind": "invalid"}])
    assert (store.records, store.cache) == before


def test_callback_cannot_mutate_stored_value():
    store = Store({})
    store.apply(
        [put("x", 0, {"items": [1]})], lambda key, record: record["value"]["items"].append(2)
    )
    assert store.read("x")["value"] == {"items": [1]}


def test_empty_batch_and_missing_delete():
    store = Store({})
    assert store.apply([]) == []
    assert store.apply([delete("absent", 0)]) == [None]
    assert store.records == store.cache == {}


def test_failed_callback_rolls_back_cold_cache_read():
    store = Store({"cold": {"version": 1, "value": [7]}})
    before = deepcopy((store.records, store.cache))

    def persist(key, record):
        assert store.read("cold")["value"] == [7]
        raise OSError("staging failed after read")

    with pytest.raises(OSError):
        store.apply([put("new", 0, [1])], persist)
    assert (store.records, store.cache) == before
