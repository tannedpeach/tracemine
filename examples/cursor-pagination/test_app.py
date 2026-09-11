from copy import deepcopy

from app import create_app


def test_stable_order_and_payload():
    items = [
        {"id": 8, "created_at": "2026-01-02T00:00:00Z", "payload": {"title": "later"}},
        {"id": 3, "created_at": "2026-01-01T00:00:00Z", "payload": {"title": "tie"}},
        {"id": 1, "created_at": "2026-01-01T00:00:00Z", "payload": {"title": "first"}},
    ]
    before = deepcopy(items)
    client = create_app(items).test_client()
    assert client.get("/items").json == {"items": [items[2], items[1], items[0]]}
    assert items == before


def test_empty_and_isolated_apps():
    empty = create_app([]).test_client()
    other = create_app([{"id": 1, "created_at": "2026-01-01", "payload": None}]).test_client()
    assert empty.get("/items").json == {"items": []}
    assert len(other.get("/items").json["items"]) == 1


def test_source_mutation_does_not_change_catalog():
    items = [{"id": 1, "created_at": "2026-01-01", "payload": {"title": "original"}}]
    client = create_app(items).test_client()
    items[0]["payload"]["title"] = "mutated"
    assert client.get("/items").json["items"][0]["payload"]["title"] == "original"
