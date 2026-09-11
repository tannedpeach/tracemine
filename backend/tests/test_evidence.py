"""The committed sample is a real recording, checked separately from test doubles."""

import json
import subprocess
import sys
from pathlib import Path

from app.store import Store

PROJECT = Path(__file__).resolve().parents[2]


def test_recorded_evidence_import_is_checked_and_idempotent(tmp_path):
    data = tmp_path / "data"
    command = [sys.executable, str(PROJECT / "scripts/import_demo.py"), "--data", str(data)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    store = Store(data)
    bundles = list((PROJECT / "examples/sample-runs").glob("*/manifest.json"))
    assert len(store.list_runs()) == len(bundles) > 0
    subprocess.run(command, check=True, capture_output=True, text=True)
    assert len(store.list_runs()) == len(bundles)
    for bundle in bundles:
        manifest = json.loads(bundle.read_text())
        run = store.get(manifest["run_id"])
        assert run.recorded and run.agent_backend == "codex"
        assert len(store.events(run.id)) > 0
        assert (store.root / "snapshots" / run.snapshot_id).is_dir()
