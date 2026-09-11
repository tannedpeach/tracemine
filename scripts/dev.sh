#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ] || [ ! -d frontend/dist ]; then
  printf 'Run ./scripts/setup.sh first.\n' >&2
  exit 1
fi
export PATH="$PWD/.venv/bin:$PATH"
# A single server serves both the API and the production-built UI on loopback.
exec python -m uvicorn app.main:app --host 127.0.0.1 --port "${PORT:-8000}"
