from api import Service


def test_current_state_order_and_detached_values():
    service = Service()
    payload = {"tags": []}
    service.catalog.put(2, 1, payload)
    service.catalog.put(1, 1, {"tags": ["first"]})
    payload["tags"].append("caller")
    rows = service.list_items()["items"]
    assert [r["id"] for r in rows] == [1, 2]
    assert rows[1]["payload"] == {"tags": []}
    rows[0]["payload"]["tags"].append("reader")
    service.catalog.delete(2)
    assert service.list_items() == {"items": [{"id": 1, "created_at": 1,
                                               "payload": {"tags": ["first"]}}]}
