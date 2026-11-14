#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
mkdir -p out/quality-adult-retarget
exec "${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}" capture --label emerald-adult-motion-retarget --json "$PWD/out/quality-adult-retarget/gpu-slot.json" --timeout 900 -- python3 tools/guarded_level_build.py retarget_adult_character.py
