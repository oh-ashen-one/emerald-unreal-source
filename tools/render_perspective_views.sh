#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
MODE="${1:-perspective}"
[[ "$MODE" == perspective || "$MODE" == camera_edges ]] || { echo "Expected perspective or camera_edges" >&2; exit 2; }
RUN_DIR="$PWD/out/quality-pass/$MODE/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"
"${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}" capture --label "emerald-$MODE-room-review" --json "$RUN_DIR/gpu-slot.json" --timeout 720 -- python3 tools/guarded_capture.py "$RUN_DIR" "$MODE"
printf '%s\n' "$RUN_DIR" > "out/quality-pass/$MODE/latest.txt"
