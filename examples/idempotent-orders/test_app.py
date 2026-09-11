import pytest

from app import create_app


def test_normalized_body_and_default_quantity():
    client = create_app().test_client()
    response = client.post("/orders", json={"sku": "  pencil  ", "ignored": "field"})
    assert response.status_code == 201
    assert response.json == {"id": 1, "sku": "pencil", "quantity": 1}


@pytest.mark.parametrize("body", [None, [], {}, {"sku": " "}, {"sku": "x", "quantity": True}, {"sku": "x", "quantity": 0}])
def test_invalid_request_leaves_no_order(body):
    client = create_app().test_client()
    assert client.post("/orders", json=body).status_code == 400
    assert client.get("/orders").json == {"orders": []}


def test_no_header_creates_distinct_orders_and_apps_are_isolated():
    client, other = create_app().test_client(), create_app().test_client()
    assert client.post("/orders", json={"sku": "x"}).json["id"] == 1
    assert client.post("/orders", json={"sku": "x"}).json["id"] == 2
    assert other.get("/orders").json == {"orders": []}
