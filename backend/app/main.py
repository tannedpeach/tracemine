"""Loopback-only API and static UI. One process owns the local run queue."""

import asyncio
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .diagnosis import read_excerpt
from .lifecycle import Runner
from .models import TERMINAL, RunRequest
from .store import Store

PROJECT = Path(__file__).resolve().parents[2]
ARTIFACTS = {
    "agent.stdout",
    "agent.stderr",
    "agent.prompt.txt",
    "baseline.stdout",
    "baseline.stderr",
    "final.stdout",
    "final.stderr",
    "final.diff",
    "diagnosis.stdout",
    "diagnosis.stderr",
    "diagnosis.input.txt",
    "agent.result.json",
    "baseline.result.json",
    "final.result.json",
}


def create_app(data_dir: Path | None = None, runner_override: Runner | None = None) -> FastAPI:
    store = (
        runner_override.store
        if runner_override
        else Store(data_dir or Path(os.environ.get("TRACEMINE_DATA", str(PROJECT / ".tracemine"))))
    )
    runner = runner_override or Runner(store)
    tasks: dict[str, asyncio.Task] = {}
    token = secrets.token_urlsafe(32)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        store.interrupt_pending()
        yield
        pending = list(tasks.values())
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

    app = FastAPI(title="TraceMine", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"]
    )

    @app.middleware("http")
    async def local_boundary(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin and urlsplit(origin).netloc != request.headers.get("host"):
            return JSONResponse(
                {"detail": "Cross-origin requests are not allowed"}, status_code=403
            )
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            if not secrets.compare_digest(request.headers.get("x-tracemine-token", ""), token):
                return JSONResponse(
                    {"detail": "Reload TraceMine to refresh the local session"}, status_code=403
                )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def required(run_id: str):
        run = store.get(run_id)
        if run is None:
            raise HTTPException(404, "Run not found")
        return run

    def launch(run):
        if len(tasks) >= 4:
            raise HTTPException(429, "Local queue is full; wait for a run to complete")
        task = asyncio.create_task(runner.run(run))
        tasks[run.id] = task
        task.add_done_callback(lambda _: tasks.pop(run.id, None))

    @app.get("/api/info")
    async def info():
        return {
            "token": token,
            "version": "0.1.0",
            "example_repo": str(PROJECT / "examples/task-cache"),
        }

    @app.get("/api/runs")
    async def list_runs():
        # Large diffs live on the detail endpoint, not on every history poll.
        return [r.model_dump(exclude={"final_diff", "diagnosis"}) for r in store.list_runs()]

    @app.post("/api/runs", status_code=202)
    async def create_run(request: RunRequest):
        if len(tasks) >= 4:
            raise HTTPException(429, "Local queue is full")
        try:
            run = runner.create(request)
        except (ValueError, OSError) as exc:
            raise HTTPException(422, str(exc)) from exc
        launch(run)
        return run

    @app.get("/api/runs/{run_id}")
    async def detail(run_id: str):
        run = required(run_id)
        logs = store.run_dir(run.id) / "logs"
        return {
            "run": run,
            "events": store.events(run.id),
            "logs": {
                name: read_excerpt(logs / name, 64000)
                for name in [
                    "baseline.stdout",
                    "baseline.stderr",
                    "final.stdout",
                    "final.stderr",
                    "agent.stderr",
                ]
            },
            "artifacts": sorted(name for name in ARTIFACTS if (logs / name).is_file()),
            "recoveries": [r for r in store.list_runs() if r.parent_run_id == run.id],
        }

    @app.post("/api/runs/{run_id}/retry", status_code=202)
    async def retry(run_id: str):
        parent = required(run_id)
        if len(tasks) >= 4:
            raise HTTPException(429, "Local queue is full")
        if any(r.parent_run_id == run_id and r.status not in TERMINAL for r in store.list_runs()):
            raise HTTPException(409, "A recovery for this run is already active")
        try:
            run = runner.create(
                RunRequest(
                    repo=parent.source_repo, task=parent.task, test_command=parent.test_command
                ),
                parent,
            )
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        launch(run)
        return run

    @app.post("/api/runs/{run_id}/cancel", status_code=202)
    async def cancel(run_id: str):
        required(run_id)
        task = tasks.get(run_id)
        if task is None:
            raise HTTPException(409, "Run is no longer active")
        task.cancel()
        return {"status": "cancellation_requested"}

    @app.get("/api/runs/{run_id}/artifacts/{name}")
    async def artifact(run_id: str, name: str):
        run = required(run_id)
        if name not in ARTIFACTS:
            raise HTTPException(404, "Artifact not found")
        path = store.run_dir(run.id) / "logs" / name
        if not path.is_file():
            raise HTTPException(404, "Artifact not available yet")
        return FileResponse(path, media_type="text/plain", filename=name)

    dist = PROJECT / "frontend/dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return app


app = create_app()
