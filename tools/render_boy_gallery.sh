#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
[[ -f unreal/Emerald/Content/QualityGallery/CharacterBoy.umap && -f data/native-boy-character-gallery-report.json ]] || { echo "Build the owned character gallery first" >&2; exit 2; }
RUN_DIR="$PWD/out/quality-pass/boy-gallery/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"
"${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}" capture --label emerald-quality-boy-gallery --json "$RUN_DIR/gpu-slot.json" --timeout 600 -- python3 tools/guarded_capture.py "$RUN_DIR" gallery /Game/QualityGallery/CharacterBoy
printf '%s\n' "$RUN_DIR" > out/quality-pass/boy-gallery/latest.txt
