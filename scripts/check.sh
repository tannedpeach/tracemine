#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$PWD/.venv/bin:$PATH"
if git grep -n "$(printf '\342\200\224')" -- .; then
  printf 'Replace prohibited punctuation in tracked source.\n' >&2
  exit 1
fi
.venv/bin/ruff check --config backend/pyproject.toml backend scripts
.venv/bin/ruff format --config backend/pyproject.toml --check backend scripts
.venv/bin/mypy backend/app --check-untyped-defs
.venv/bin/pytest backend/tests -q
npm --prefix frontend run format:check
npm --prefix frontend run build
