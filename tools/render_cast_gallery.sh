#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
[[ -f unreal/Emerald/Content/QualityGallery/Cast.umap ]] || { echo "Build owned cast gallery first" >&2; exit 2; }
RUN_DIR="$PWD/out/quality-pass/cast-gallery/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"
"${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}" capture --label emerald-cast-gallery --json "$RUN_DIR/gpu-slot.json" --timeout 900 -- python3 tools/guarded_capture.py "$RUN_DIR" gallery /Game/QualityGallery/Cast
printf '%s\n' "$RUN_DIR" > out/quality-pass/cast-gallery/latest.txt
