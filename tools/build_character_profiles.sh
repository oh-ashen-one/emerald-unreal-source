#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
python3 tools/compile_character_profiles.py
GPU_SLOT="${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}"
mkdir -p out/character-import
"$GPU_SLOT" capture --label emerald-character-profiles --json "$PWD/out/character-import/profile-gpu.json" --timeout 600 -- python3 tools/guarded_level_build.py build_character_profiles.py
if [[ -f unreal/Emerald/Content/Imported/Data/quality-girl-profile.json ]]; then python3 tools/install_quality_character.py; fi
if [[ -f unreal/Emerald/Content/Imported/Data/quality-adult-profile.json && -f data/native-adult-integration-report.json ]]; then python3 tools/install_adult_character.py; fi

if [[ -f unreal/Emerald/Content/Imported/Data/quality-boy-profile.json && -f data/native-boy-integration-report.json ]]; then python3 tools/install_boy_character.py; fi
if [[ -f data/native-cast-integration-report.json ]]; then python3 tools/install_cast_characters.py; fi
if [[ -f data/native-parent-integration-report.json ]]; then python3 tools/install_parent_characters.py; fi
