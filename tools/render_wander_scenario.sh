#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
GPU_SLOT="${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}"
[ -x "$GPU_SLOT" ] || { echo "Shared GPU guard required" >&2; exit 2; }
[ -f unreal/Emerald/Content/Maps/LittlerootTown.umap ] || { echo "Build all six maps first" >&2; exit 2; }
RUN_DIR="$PWD/out/wander/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"
"$GPU_SLOT" capture --label emerald-source-wander-render --json "$RUN_DIR/gpu-slot.json" --timeout 720 -- python3 tools/guarded_capture.py "$RUN_DIR" wander
printf '%s\n' "$RUN_DIR" > out/wander/latest.txt
