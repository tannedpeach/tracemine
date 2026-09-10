#!/usr/bin/env python3
"""Run the same lifecycle as the web app, without a web server."""
import argparse
import asyncio
from pathlib import Path
from app.lifecycle import Runner
from app.models import RunRequest
from app.store import Store


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo")
    parser.add_argument("task")
    parser.add_argument("--test-command", required=True)
    parser.add_argument("--data", type=Path, default=Path(".tracemine"))
    args = parser.parse_args()
    store = Store(args.data)
    runner = Runner(store)
    run = runner.create(RunRequest(repo=args.repo, task=args.task, test_command=args.test_command))
    print(f"Run {run.id}", flush=True)
    await runner.run(run)
    print(run.model_dump_json(indent=2))
    return 0 if run.status == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
