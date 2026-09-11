#!/usr/bin/env python3
"""Export a reviewed local run as a redacted, checksummed evidence bundle.

The original byte streams remain in local storage. This produces distinct public
copies; it does not claim that redacted files are byte-identical to originals.
"""

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

from app.models import TERMINAL
from app.store import Store

PROJECT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    parser.add_argument("--data", type=Path, default=PROJECT / ".tracemine")
    args = parser.parse_args()
    store = Store(args.data)
    run = store.get(args.run_id)
    if not run or run.status not in TERMINAL or run.agent_backend != "codex":
        raise SystemExit("Only a completed real run can be exported")
    root = PROJECT / "examples/sample-runs" / run.id
    if root.exists():
        raise SystemExit(
            "Bundle already exists; review it instead of silently overwriting evidence"
        )
    root.mkdir(parents=True)
    replacements = [
        (str(store.run_dir(run.id)), "<RUN>"),
        (run.source_repo, "<SOURCE>"),
        (str(PROJECT), "<TRACEMINE>"),
        (str(Path.home()), "<HOME>"),
    ]

    def redact(text: str) -> str:
        for source, replacement in sorted(
            replacements, key=lambda pair: len(pair[0]), reverse=True
        ):
            text = text.replace(source, replacement)
        text = re.sub(r"(?:/private)?/var/folders/[^/\s]+/[^/\s]+/T", "<TEMP>", text)
        return text

    manifest = {
        "format": 1,
        "kind": "redacted-real-run",
        "run_id": run.id,
        "source_name": Path(run.source_repo).name,
        "redaction": "Local source, run, project, home and temporary path prefixes replaced with named placeholders. Original bytes retained locally.",
        "files": {},
    }
    paths = [store.run_dir(run.id) / "run.json", store.run_dir(run.id) / "events.normalized.jsonl"]
    paths += sorted((store.run_dir(run.id) / "logs").glob("*"))
    for path in paths:
        if not path.is_file():
            continue
        original = path.read_bytes()
        published = redact(original.decode("utf-8", errors="replace")).encode()
        relative = path.relative_to(store.run_dir(run.id))
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(published)
        manifest["files"][str(relative)] = {
            "original_sha256": hashlib.sha256(original).hexdigest(),
            "published_sha256": hashlib.sha256(published).hexdigest(),
        }
    shutil.copytree(store.root / "snapshots" / run.snapshot_id, root / "input")
    for path in sorted((root / "input").rglob("*")):
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest["files"][str(path.relative_to(root))] = {
                "original_sha256": digest,
                "published_sha256": digest,
            }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Exported {run.id}. Review source, prompts and every artifact before publishing.")


if __name__ == "__main__":
    main()
