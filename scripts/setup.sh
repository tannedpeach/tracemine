#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v python3 >/dev/null
command -v node >/dev/null
command -v npm >/dev/null
command -v git >/dev/null
python3 -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11+ required"'
node -e 'if (Number(process.versions.node.split(".")[0]) < 20) throw Error("Node 20+ required")'
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps -e backend
npm --prefix frontend ci
npm --prefix frontend run build
.venv/bin/python scripts/import_demo.py
printf '\nReady. Start with: ./scripts/dev.sh\n'
