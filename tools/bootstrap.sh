#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
SOURCE_REV=$(python3 -c 'import json;print(json.load(open("data/source-lock.json"))["revision"])')
if [ ! -d pokeemerald/.git ]; then
  git clone https://github.com/pret/pokeemerald.git pokeemerald
  git -C pokeemerald checkout --detach "$SOURCE_REV"
fi
CURRENT_REV=$(git -C pokeemerald rev-parse HEAD)
if [ "$CURRENT_REV" != "$SOURCE_REV" ]; then
  echo "Source revision differs from source-lock.json; preserve local source changes and check out the pinned revision yourself." >&2
  exit 1
fi
python3 tools/import_littleroot.py
python3 tools/compile_events.py
python3 -m unittest discover -s tests -v
