#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
[[ -f unreal/Emerald/Content/QualityGallery/InteriorFixtures.umap && -f data/native-fixture-gallery-report.json ]] || { echo "Build the owned fixture gallery first" >&2; exit 2; }
RUN_DIR="$PWD/out/quality-pass/fixture-gallery/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"
"${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}" capture --label emerald-quality-fixture-gallery --json "$RUN_DIR/gpu-slot.json" --timeout 600 -- python3 tools/guarded_capture.py "$RUN_DIR" gallery /Game/QualityGallery/InteriorFixtures
printf '%s\n' "$RUN_DIR" > out/quality-pass/fixture-gallery/latest.txt
