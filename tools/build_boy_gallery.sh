#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
mkdir -p out/quality-boy-gallery-build
exec "${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}" capture --label emerald-boy-gallery-build --json "$PWD/out/quality-boy-gallery-build/gpu-slot.json" --timeout 1200 -- python3 tools/guarded_level_build.py build_boy_gallery.py
