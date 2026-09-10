from app import create_app


def test_read_and_update():
    client = create_app().test_client()
    assert client.get("/issues/1").json["status"] == "open"
    assert client.patch("/issues/1", json={"status": "closed"}).status_code == 200
    assert client.get("/issues/1").json["status"] == "closed"


def test_missing():
    client = create_app().test_client()
    assert client.get("/issues/99").status_code == 404
    assert client.patch("/issues/99", json={"status": "closed"}).status_code == 404


def test_independent_apps():
    first, second = create_app().test_client(), create_app().test_client()
    first.patch("/issues/1", json={"title": "Changed"})
    assert second.get("/issues/1").json["title"] == "Document the API"
