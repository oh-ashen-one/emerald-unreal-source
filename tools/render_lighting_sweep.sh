#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
GPU_SLOT="${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}"
RUN_DIR="$PWD/out/lighting/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"
"$GPU_SLOT" capture --label emerald-skylight-calibration --json "$RUN_DIR/gpu-slot.json" --timeout 720 -- python3 tools/guarded_capture.py "$RUN_DIR" lighting "${1:-1,100,1000,5000}"
printf '%s\n' "$RUN_DIR" > out/lighting/latest.txt
