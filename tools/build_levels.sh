#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
UE_ROOT="${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}"
GPU_SLOT="${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}"
[ -x "$GPU_SLOT" ] || { echo "Shared GPU guard required" >&2; exit 2; }
mkdir -p out/source-reference
python3 tools/import_littleroot.py --references out/source-reference > out/source-reference/import-summary.json
python3 tools/source_style.py
python3 tools/bake_static_glb.py
python3 tools/build_quality_terrain.py
python3 tools/prepare_quality_furniture.py
python3 tools/prepare_quality_grass.py
python3 tools/prepare_quality_lawn.py
python3 tools/prepare_quality_fixtures.py
python3 tools/prepare_furnishing_variants.py
python3 tools/prepare_interior_details.py
python3 tools/prepare_lab_metal.py
python3 tools/build_original_lab_analyzer.py
mkdir -p out/level-build
exec "$GPU_SLOT" capture --label emerald-import-six-maps --json "$PWD/out/level-build/gpu-slot.json" --timeout 1200 -- \
 python3 tools/guarded_level_build.py
