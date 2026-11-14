#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
python3 tools/prepare_characters.py
GPU_SLOT="${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}"
mkdir -p out/character-import
exec "$GPU_SLOT" capture --label emerald-native-skeletal-import --json "$PWD/out/character-import/gpu-slot.json" --timeout 1200 -- "${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}/Engine/Binaries/Mac/UnrealEditor-Cmd" "$PWD/unreal/Emerald/Emerald.uproject" -run=pythonscript "-script=$PWD/tools/import_characters.py" -nullrhi -unattended -nosound -nosplash -NoCrashReports "-abslog=$PWD/out/character-import/engine.log"
