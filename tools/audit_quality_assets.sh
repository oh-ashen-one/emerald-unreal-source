#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
UE_ROOT="${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}"
GPU_SLOT="${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}"
SCRIPT="${1:-audit_quality_assets.py}"
[[ "$SCRIPT" == audit_quality_assets.py || "$SCRIPT" == audit_quality_materials.py || "$SCRIPT" == audit_fab_quality.py ]] || { echo "Unknown read-only audit" >&2; exit 2; }
mkdir -p out/quality-asset-audit
"$GPU_SLOT" capture --label emerald-quality-asset-audit --json "$PWD/out/quality-asset-audit/gpu-slot.json" --timeout 600 -- \
 "$UE_ROOT/Engine/Binaries/Mac/UnrealEditor-Cmd" "$PWD/unreal/Emerald/Emerald.uproject" \
 -run=pythonscript "-script=$PWD/tools/$SCRIPT" -nullrhi -unattended -nosound -nosplash -NoCrashReports \
 "-abslog=$PWD/out/quality-asset-audit/engine.log"
