#!/bin/bash
# Called only beneath the shared guard; do not invoke directly.
set -euo pipefail
[ "${GPU_SLOT_HELD:-}" ] || { echo "Launch through Open Emerald.command" >&2; exit 2; }
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
UE_ROOT="${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}"
exec /usr/bin/open -n -W "$UE_ROOT/Engine/Binaries/Mac/UnrealEditor.app" --args \
 "$PWD/unreal/Emerald/Emerald.uproject" /Game/Maps/LittlerootTown -game -windowed \
 -ResX=1600 -ResY=1000 "-dpcvars=t.MaxFPS=${GPU_SLOT_FPS_CAP:-60}" -NoCrashReports -DisablePython
