#!/usr/bin/env python3
"""Load the bundled, checksummed real recordings into local history. No model calls."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from app.models import Event, Run
from app.store import Store

PROJECT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=PROJECT / ".tracemine")
    args = parser.parse_args()
    store = Store(args.data)
    with store.claim():
        for bundle in sorted((PROJECT / "examples/sample-runs").glob("*/manifest.json")):
            root = bundle.parent
            manifest = json.loads(bundle.read_text())
            for name, hashes in manifest["files"].items():
                path = (root / name).resolve()
                if root.resolve() not in path.parents or not path.is_file():
                    raise ValueError(f"Invalid bundle path: {name}")
                if hashlib.sha256(path.read_bytes()).hexdigest() != hashes["published_sha256"]:
                    raise ValueError(f"Evidence checksum mismatch: {name}")
            run = Run.model_validate_json((root / "run.json").read_text())
            if store.get(run.id):
                continue
            run.recorded = True
            source_name = manifest.get("source_name", "task-cache")
            if Path(source_name).name != source_name:
                raise ValueError("Invalid fixture name")
            run.source_repo = str(PROJECT / "examples" / source_name)
            run.working_repo = (
                "Recorded evidence; use Retry with diagnosis to create a new working copy"
            )
            saved = store.root / "snapshots" / run.snapshot_id
            if not saved.exists():
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(root / "input", saved)
            target = store.run_dir(run.id)
            target.mkdir(parents=True, exist_ok=True)
            if (root / "logs").exists():
                shutil.copytree(root / "logs", target / "logs")
            store.save(run)
            for line in (root / "events.normalized.jsonl").read_text().splitlines():
                store.add_event(run.id, Event.model_validate_json(line))
            store.export_metadata(run)
            print(f"Loaded real recording {run.id[:8]} ({run.status})")


if __name__ == "__main__":
    main()
