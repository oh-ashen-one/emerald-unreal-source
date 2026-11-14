#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
python3 tools/prepare_adult_character.py
mkdir -p out/quality-adult-import
touch out/quality-adult-import/start-marker
"${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}" capture --label emerald-adult-character-import --json "$PWD/out/quality-adult-import/gpu-slot.json" --timeout 1200 -- python3 tools/guarded_level_build.py import_adult_character.py
python3 - <<'PY'
from pathlib import Path
import json
p=Path('data/native-adult-character-import-report.json')
if not p.is_file() or p.stat().st_mtime<Path('out/quality-adult-import/start-marker').stat().st_mtime:raise SystemExit('No fresh native adult import report; editor exit alone is insufficient')
r=json.loads(p.read_text())
if not r['meshes']:raise SystemExit('Native adult assembly absent')
print('Verified fresh native adult import report; visual/rig quality remains unaccepted')
PY
