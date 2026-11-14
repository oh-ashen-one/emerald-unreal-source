#!/usr/bin/env python3
"""Stage only pinned, owner-authorized free Fab native assets from owned cache."""
import hashlib
import json
import os
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
cache=Path(os.environ.get('FAB_VAULT_ROOT','/Users/Shared/UnrealEngine/Launcher/VaultCache')).resolve()
content=ROOT/'unreal/Emerald/Content'
for asset in json.loads((ROOT/'data/fab-quality-lock.json').read_text())['assets']:
    source=cache/asset['cache_content_relative']
    for item in asset['files']:
        p=source/item['path'];target=content/item['path']
        if not p.resolve().is_relative_to(source.resolve()) or not target.resolve().is_relative_to(content.resolve()):raise SystemExit('Unsafe Fab asset path')
        if p.stat().st_size!=item['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise SystemExit('Owned cached Fab input differs from lock')
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=item['sha256']:raise SystemExit('Existing project asset differs; preserved')
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():shutil.copyfile(p,target)
print('Verified selected free Fab native source files; owned cache unchanged')

ledger=ROOT/'docs/QUALITY_ASSETS.md'
if ledger.is_file():
    target=ROOT/'out/quality-pass/ASSETS.md';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(ledger.read_text())
