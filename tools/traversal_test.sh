#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
UE_ROOT="${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}"
GPU_SLOT="${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}"
MODE="${1:-overhead}"
[[ "$MODE" == overhead || "$MODE" == thirdperson ]] || { echo "Expected overhead or thirdperson" >&2; exit 2; }
TRAVERSAL_ARGS=(-EmeraldSmoke)
[[ "$MODE" != thirdperson ]] || TRAVERSAL_ARGS+=(-EmeraldThirdPerson)
[ -x "$GPU_SLOT" ] || { echo "Shared GPU guard required" >&2; exit 2; }
[ -f unreal/Emerald/Content/Maps/LittlerootTown.umap ] || { echo "Run tools/build_levels.sh first" >&2; exit 2; }
python3 tools/plan_traversal.py
RUN_DIR="$PWD/out/traversal/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"
"$GPU_SLOT" capture --label emerald-input-traversal --json "$RUN_DIR/gpu-slot.json" --timeout 600 -- \
 python3 tools/engine_launch_budget.py --label input-traversal --exec "$UE_ROOT/Engine/Binaries/Mac/UnrealEditor-Cmd" "$PWD/unreal/Emerald/Emerald.uproject" \
 /Game/Maps/LittlerootTown -game -nullrhi -unattended -nosound -nosplash -NoCrashReports -DisablePython \
 "${TRAVERSAL_ARGS[@]}" "-EmeraldSmokeReport=$RUN_DIR/result.json" "-abslog=$RUN_DIR/engine.log"
python3 - "$RUN_DIR/result.json" "$MODE" <<'PY'
import json,sys,re
from pathlib import Path
x=json.load(open(sys.argv[1],encoding='utf-8-sig'))
assert x['success'] and x['distinct_actual_warp_links']==13
assert x['completed_input_steps']==x['planned_input_steps'] and x['planned_input_steps']>0
x['camera_mode']=sys.argv[2]
if sys.argv[2]=='thirdperson':
    log=(Path(sys.argv[1]).parent/'engine.log').read_text()
    states=re.findall(r'EMERALD_ROOM_VIEW map=(\S+) perspective=(\d+)',log)
    assert len({name for name,_ in states})==6 and all(value=='1' for _,value in states)
    x['third_person_initialization_all_six_maps']=True
Path(sys.argv[1]).write_text(json.dumps(x,indent=2)+'\n')
print('Verified actual C++ grid input traversal:',x)
PY
printf '%s\n' "$RUN_DIR" > out/traversal/latest.txt
