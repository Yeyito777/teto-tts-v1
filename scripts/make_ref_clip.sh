#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 4 ]]; then
  echo "usage: $0 <input.wav> <start_seconds> [duration_seconds=20] [output.wav]" >&2
  exit 1
fi

infile=$1
start=$2
length=${3:-20}
outfile=${4:-}

if [[ -z "$outfile" ]]; then
  base=$(basename "$infile")
  base=${base%.wav}
  safe_start=$(printf '%s' "$start" | tr '.' 'p')
  safe_len=$(printf '%s' "$length" | tr '.' 'p')
  outfile="$(dirname "$infile")/../clips/${base}-${safe_start}s-${safe_len}s.wav"
fi

mkdir -p "$(dirname "$outfile")"
ffmpeg -y -ss "$start" -t "$length" -i "$infile" -ac 1 -ar 24000 "$outfile" >/dev/null 2>&1
printf '%s\n' "$outfile"
