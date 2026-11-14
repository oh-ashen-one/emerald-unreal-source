#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
GPU_SLOT="${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}"
mkdir -p out/village-gallery-build
exec "$GPU_SLOT" capture --label emerald-village-asset-gallery --json "$PWD/out/village-gallery-build/gpu-slot.json" --timeout 900 -- python3 tools/guarded_level_build.py build_village_gallery.py
