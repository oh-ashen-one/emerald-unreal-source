#!/bin/bash
# Source after cd to project root, before any editor/game launch.
emerald_require_native() {
  if [ ! -f unreal/Emerald/Binaries/Mac/libUnrealEditor-Emerald.dylib ]; then
    echo "Native Emerald module is absent. Run tools/build.sh before launching Unreal." >&2
    return 2
  fi
  python3 tools/engine_launch_budget.py --check || return 81
}
