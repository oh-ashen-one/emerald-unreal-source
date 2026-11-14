#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
PHASE="${1:-before}"
[[ "$PHASE" == before || "$PHASE" == after ]] || { echo "Expected before or after" >&2; exit 2; }
if [[ "$PHASE" == after && ! -f data/quality-camera-lock.json ]]; then echo "Capture and inspect before views first" >&2; exit 2; fi
if [[ "$PHASE" == before && -f data/quality-camera-lock.json ]]; then echo "The historical before reference is locked; use after for current quality art." >&2; exit 2; fi
GPU_SLOT="${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}"
RUN_DIR="$PWD/out/quality-pass/$PHASE/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"
"$GPU_SLOT" capture --label "emerald-quality-$PHASE" --json "$RUN_DIR/gpu-slot.json" --timeout 720 -- python3 tools/guarded_capture.py "$RUN_DIR" quality
printf '%s\n' "$RUN_DIR" > "out/quality-pass/$PHASE/latest.txt"
