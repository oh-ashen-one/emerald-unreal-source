#!/bin/bash
# CPU-only Unreal automation, still admitted by the shared engine launch guard.
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
UE_ROOT="${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}"
GPU_SLOT="${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}"
[ -x "$GPU_SLOT" ] || { echo "Shared gpu_slot guard required" >&2; exit 2; }
RUN_DIR="$PWD/out/data-test/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"
"$GPU_SLOT" capture --label emerald-source-data-tests --json "$RUN_DIR/gpu-slot.json" --timeout 600 -- \
  python3 tools/engine_launch_budget.py --label source-data-tests --exec "$UE_ROOT/Engine/Binaries/Mac/UnrealEditor-Cmd" "$PWD/unreal/Emerald/Emerald.uproject" \
  -nullrhi -unattended -nosound -nosplash -NoCrashReports -NoZenAutoLaunch \
  '-ExecCmds=Automation RunTests Emerald' '-TestExit=Automation Test Queue Empty' \
  "-ReportExportPath=$RUN_DIR/report" "-abslog=$RUN_DIR/engine.log"

python3 tools/verify_automation.py "$RUN_DIR/report/index.json" --prefix Emerald
printf "%s\n" "$RUN_DIR" > out/data-test/latest.txt
