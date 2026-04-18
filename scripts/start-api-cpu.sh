#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
exec "$ROOT/.venv/bin/python" run_server.py \
  --host 127.0.0.1 \
  --port 8011 \
  --llm-base-url http://127.0.0.1:8010/v1 \
  --device cpu \
  --presets-dir "$ROOT/refs/presets" \
  --log-level info
