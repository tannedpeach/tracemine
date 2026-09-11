from app import create_app
import app as app_module
import pytest
from unittest.mock import Mock


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


@pytest.fixture
def cache_probe(monkeypatch):
    clock = Mock(return_value=100.0)
    loader = Mock(wraps=app_module._load_issue)
    monkeypatch.setattr(app_module, "monotonic", clock)
    monkeypatch.setattr(app_module, "_load_issue", loader)
    return clock, loader


def test_cache_hit_and_expiry(cache_probe):
    clock, loader = cache_probe
    client = create_app().test_client()
    original = client.get("/issues/1")
    assert original.status_code == 200
    assert original.json == {"id": 1, "title": "Document the API", "status": "open"}
    assert original.mimetype == "application/json"
    assert loader.call_count == 1
    clock.return_value = 159.999
    cached = client.get("/issues/1")
    assert cached.status_code == original.status_code
    assert cached.data == original.data
    assert cached.headers == original.headers
    assert loader.call_count == 1
    # Hits do not extend the TTL, and the boundary itself is expired.
    clock.return_value = 160.0
    assert client.get("/issues/1").json == original.json
    assert loader.call_count == 2
    clock.return_value = 219.999
    assert client.get("/issues/1").json == original.json
    assert loader.call_count == 2
    clock.return_value = 220.0
    assert client.get("/issues/1").json == original.json
    assert loader.call_count == 3


def test_patch_invalidates_cache(cache_probe):
    _, loader = cache_probe
    client = create_app().test_client()
    client.get("/issues/1")
    updated = client.patch("/issues/1", json={"title": "Changed", "status": "closed"})
    assert updated.status_code == 200
    assert updated.json == {"id": 1, "title": "Changed", "status": "closed"}
    assert client.get("/issues/1").json == updated.json
    assert loader.call_count == 2
    assert client.get("/issues/1").json == updated.json
    assert loader.call_count == 2


def test_missing_issues_are_not_cached(cache_probe):
    _, loader = cache_probe
    client = create_app().test_client()
    for _ in range(2):
        missing = client.get("/issues/99")
        assert missing.status_code == 404
        assert missing.json == {"error": "not found"}
    assert loader.call_count == 2
    missing_patch = client.patch("/issues/99", json={"title": "New"})
    assert missing_patch.status_code == 404
    assert missing_patch.json == {"error": "not found"}
    assert client.get("/issues/99").status_code == 404
    assert client.get("/issues/1").status_code == 200


def test_caches_are_independent(cache_probe):
    _, loader = cache_probe
    first, second = create_app().test_client(), create_app().test_client()
    original = first.get("/issues/1").json
    assert second.get("/issues/1").json == original
    assert loader.call_count == 2
    first.patch("/issues/1", json={"title": "Changed"})
    assert second.get("/issues/1").json == original
    assert loader.call_count == 2
    assert first.get("/issues/1").json["title"] == "Changed"
    assert loader.call_count == 3
