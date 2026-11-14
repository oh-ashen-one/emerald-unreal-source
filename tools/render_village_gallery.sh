#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
GPU_SLOT="${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}"
RUN_DIR="$PWD/out/quality-pass/gallery/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"
"$GPU_SLOT" capture --label emerald-village-gallery-capture --json "$RUN_DIR/gpu-slot.json" --timeout 600 -- python3 tools/guarded_capture.py "$RUN_DIR" gallery /Game/QualityGallery/VillageParts
printf '%s\n' "$RUN_DIR" > out/quality-pass/gallery/latest.txt
