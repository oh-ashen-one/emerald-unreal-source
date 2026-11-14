#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
python3 tools/prepare_quality_motion_source.py
mkdir -p out/quality-character-retarget
exec "${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}" capture --label emerald-quality-character-retarget --json "$PWD/out/quality-character-retarget/gpu-slot.json" --timeout 1200 -- python3 tools/guarded_level_build.py retarget_quality_character.py
