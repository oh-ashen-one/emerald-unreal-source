#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
python3 tools/prepare_quality_character.py
mkdir -p out/quality-character-import
exec "${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}" capture --label emerald-quality-character-import --json "$PWD/out/quality-character-import/gpu-slot.json" --timeout 1200 -- python3 tools/guarded_level_build.py import_quality_character.py
