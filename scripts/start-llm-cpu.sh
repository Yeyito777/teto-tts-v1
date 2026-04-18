#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
export LD_LIBRARY_PATH="$ROOT/vendor/llamacpp:${LD_LIBRARY_PATH:-}"
exec "$ROOT/vendor/llamacpp/llama-server" \
  -m "$ROOT/models/MioTTS-GGUF/MioTTS-0.1B-BF16.gguf" \
  -c 4096 \
  --host 127.0.0.1 \
  --port 8010 \
  --batch-size 4 \
  --threads 4 \
  --n-gpu-layers 0
