from fastapi.testclient import TestClient

from app.lifecycle import Runner
from app.main import create_app
from app.models import RunRequest
from app.store import Store


def test_api_local_boundary_and_input_errors(tmp_path):
    app = create_app(tmp_path / "data")
    with TestClient(app) as client:
        info = client.get("/api/info").json()
        headers = {"x-tracemine-token": info["token"]}
        assert client.post("/api/runs", json={}).status_code == 403
        assert client.post("/api/runs", json={}, headers=headers).status_code == 422
        assert (
            client.get("/api/info", headers={"origin": "https://evil.example"}).status_code == 403
        )
        assert client.get("/api/info", headers={"host": "evil.example"}).status_code == 400
        assert client.get("/api/runs/no-such-run").status_code == 404
        assert client.get("/api/runs").json() == []
        response = client.post(
            "/api/runs",
            headers=headers,
            json={"repo": str(tmp_path / "missing"), "task": "change", "test_command": "true"},
        )
        assert response.status_code == 422


def test_interrupted_runs_and_artifact_allowlist(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("pass\n")
    store = Store(tmp_path / "data")
    run = Runner(store).create(RunRequest(repo=str(source), task="change", test_command="true"))
    app = create_app(runner_override=Runner(store))
    with TestClient(app) as client:
        detail = client.get(f"/api/runs/{run.id}").json()
        assert detail["run"]["status"] == "error"
        assert "Server stopped" in detail["run"]["error"]
        assert client.get(f"/api/runs/{run.id}/artifacts/runs.sqlite3").status_code == 404
        headers = {"x-tracemine-token": client.get("/api/info").json()["token"]}
        assert client.post(f"/api/runs/{run.id}/retry", json={}, headers=headers).status_code == 409
