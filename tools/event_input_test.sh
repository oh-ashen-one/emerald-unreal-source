#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
UE_ROOT="${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}"
GPU_SLOT="${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}"
[ -x "$GPU_SLOT" ] || { echo "Shared GPU guard required" >&2; exit 2; }
RUN_DIR="$PWD/out/event-input/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"
"$GPU_SLOT" capture --label emerald-source-keyboard-test --json "$RUN_DIR/gpu-slot.json" --timeout 600 -- \
 python3 tools/engine_launch_budget.py --label source-keyboard --exec "$UE_ROOT/Engine/Binaries/Mac/UnrealEditor-Cmd" "$PWD/unreal/Emerald/Emerald.uproject" /Game/Maps/LittlerootTown \
 -game -nullrhi -unattended -nosound -nosplash -NoCrashReports -DisablePython -EmeraldEventSmoke \
 "-EmeraldEventReport=$RUN_DIR/result.json" "-abslog=$RUN_DIR/engine.log"
python3 - "$RUN_DIR/result.json" <<'PY'
import json,sys
x=json.load(open(sys.argv[1],encoding='utf-8-sig'))
assert x['success'] and x['stage']==5 and not x['last_source_error']
assert [x['player_x'],x['player_y']]==[10,2] and [x['twin_x'],x['twin_y']]==[7,2]
print('Verified source keyboard/input scenario:',x)
PY
printf '%s\n' "$RUN_DIR" > out/event-input/latest.txt
