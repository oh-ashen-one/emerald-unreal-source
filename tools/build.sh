#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
UE_ROOT="${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}"
python3 tools/import_littleroot.py
python3 tools/compile_events.py
exec /usr/sbin/taskpolicy -b "$UE_ROOT/Engine/Build/BatchFiles/Mac/Build.sh" EmeraldEditor Mac Development "-project=$PWD/unreal/Emerald/Emerald.uproject" -MaxParallelActions=4
