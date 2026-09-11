"""SQLite owns metadata; the filesystem owns immutable inputs and raw process logs."""

import fcntl
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .models import TERMINAL, Event, Run


class Store:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.database = self.root / "runs.sqlite3"
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    run_id TEXT NOT NULL, sequence INTEGER NOT NULL, data TEXT NOT NULL,
                    PRIMARY KEY (run_id, sequence), FOREIGN KEY(run_id) REFERENCES runs(id));
            """)

    @contextmanager
    def claim(self):
        """Only one server or CLI process can own a run database at a time."""
        with (self.root / "owner.lock").open("a") as lock:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise RuntimeError("This data directory is already in use by TraceMine") from exc
            try:
                yield
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.database, timeout=10)
        try:
            db.execute("PRAGMA foreign_keys=ON")
            with db:
                yield db
        finally:
            db.close()

    def save(self, run: Run) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT INTO runs VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
                (run.id, run.model_dump_json()),
            )

    def get(self, run_id: str) -> Run | None:
        with self.connect() as db:
            row = db.execute("SELECT data FROM runs WHERE id=?", (run_id,)).fetchone()
        return Run.model_validate_json(row[0]) if row else None

    def list_runs(self) -> list[Run]:
        with self.connect() as db:
            rows = db.execute("SELECT data FROM runs ORDER BY rowid DESC LIMIT 100").fetchall()
        return [Run.model_validate_json(row[0]) for row in rows]

    def add_event(self, run_id: str, event: Event) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT INTO events VALUES (?, ?, ?)",
                (run_id, event.sequence, event.model_dump_json()),
            )

    def events(self, run_id: str) -> list[Event]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT data FROM events WHERE run_id=? ORDER BY sequence", (run_id,)
            ).fetchall()
        return [Event.model_validate_json(row[0]) for row in rows]

    def run_dir(self, run_id: str) -> Path:
        # IDs never come directly from a path parameter: callers first look up metadata.
        return self.root / "runs" / run_id

    def interrupt_pending(self) -> None:
        with self.connect() as db:
            rows = db.execute("SELECT data FROM runs").fetchall()
        for row in rows:
            run = Run.model_validate_json(row[0])
            if run.status not in TERMINAL:
                run.status = "error"
                run.error = "Server stopped before this run completed. Logs remain available."
                self.save(run)

    def export_metadata(self, run: Run) -> None:
        target = self.run_dir(run.id)
        target.mkdir(parents=True, exist_ok=True)
        (target / "run.json").write_text(run.model_dump_json(indent=2))
        (target / "events.normalized.jsonl").write_text(
            "".join(json.dumps(e.model_dump()) + "\n" for e in self.events(run.id))
        )
