#!/usr/bin/env python3
"""Stage only locked installed Epic Example assets, keeping native package paths."""
import hashlib
import json
import os
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
lock=json.loads((ROOT/'data/epic-quality-lock.json').read_text())
engine=Path(os.environ.get('UE_ROOT','/Users/Shared/Epic Games/UE_5.8')).resolve()
source=engine/lock['source_root'];content=ROOT/'unreal/Emerald/Content'
for item in lock['files']:
    path=source/item['source'];target=content/item['target']
    if not path.resolve().is_relative_to(source.resolve()) or not target.resolve().is_relative_to(content.resolve()):raise SystemExit('Unsafe native asset path')
    if path.stat().st_size!=item['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise SystemExit('Installed Example differs from lock: '+item['source'])
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=item['sha256']:raise SystemExit('Existing project asset differs; preserved: '+item['target'])
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():shutil.copyfile(path,target)
print('Verified/staged',len(lock['files']),'installed Epic Example files; no download/account change')
