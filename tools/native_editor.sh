#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
UE_ROOT="${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}"
GPU_SLOT="${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}"
[ -x "$GPU_SLOT" ] || { echo "Shared GPU guard required" >&2; exit 2; }
mkdir -p out/native-editor
exec "$GPU_SLOT" capture --label emerald-native-editor --json "$PWD/out/native-editor/gpu-slot.json" --timeout 1200 -- python3 tools/owned_native_editor.py
