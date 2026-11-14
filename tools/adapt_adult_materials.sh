#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
mkdir -p out/quality-adult-materials
exec "${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}" capture --label emerald-adult-pbr-adapter --json "$PWD/out/quality-adult-materials/gpu-slot.json" --timeout 900 -- python3 tools/guarded_level_build.py adapt_adult_materials.py
