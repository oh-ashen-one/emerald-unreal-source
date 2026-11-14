#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
python3 tools/prepare_boy_character.py
mkdir -p out/quality-boy-import
exec "${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}" capture --label emerald-boy-character-import --json "$PWD/out/quality-boy-import/gpu-slot.json" --timeout 1200 -- python3 tools/guarded_level_build.py import_boy_character.py
