#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/require_native.sh
emerald_require_native
RUN_DIR="$PWD/out/quality-pass/parent-contacts/$(date +%Y%m%d-%H%M%S)"
for CONTACT_ROOM in Brendan May; do
  mkdir -p "$RUN_DIR/$CONTACT_ROOM"
  "${GPU_SLOT:-$HOME/.cache/gpu-slot/bin/gpu_slot.sh}" capture --label "emerald-parent-contact-$CONTACT_ROOM" --json "$RUN_DIR/$CONTACT_ROOM/gpu-slot.json" --timeout 900 -- python3 tools/guarded_capture.py "$RUN_DIR/$CONTACT_ROOM" contacts "/Game/QualityGallery/Parent${CONTACT_ROOM}Room"
done
printf '%s\n' "$RUN_DIR" > out/quality-pass/parent-contacts/latest.txt
