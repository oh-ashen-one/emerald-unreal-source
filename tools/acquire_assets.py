#!/usr/bin/env python3
"""Acquire only the selected CC0 pack subtrees; preserve existing source changes."""
import hashlib
import json
from pathlib import Path
import subprocess
from acquire_props import acquire as acquire_props

ROOT=Path(__file__).resolve().parents[1]
lock=json.loads((ROOT/'data/asset-lock.json').read_text())
acquire_props()
kenney=[item for item in lock['files'] if item.get('source','kenney')=='kenney']
repo=ROOT/'.references/kenney'
if not repo.exists():
    subprocess.run(['git','clone','--depth','1','--filter=blob:none','--sparse',lock['repository'],str(repo)],check=True)
    subprocess.run(['git','-C',str(repo),'fetch','--depth','1','origin',lock['revision']],check=True)
    subprocess.run(['git','-C',str(repo),'checkout','--detach',lock['revision']],check=True)
    subprocess.run(['git','-C',str(repo),'sparse-checkout','set',*sorted({item['pack'] for item in kenney})],check=True)
current=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
if current!=lock['revision']:
    raise SystemExit('Existing candidate checkout differs from asset-lock; preserved without changes')
missing=sorted({item['pack'] for item in kenney if not (ROOT/item['path']).exists()})
if missing:
    subprocess.run(['git','-C',str(repo),'sparse-checkout','add',*missing],check=True)
for item in lock['files']:
    path=ROOT/item['path']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
        raise SystemExit('Candidate hash differs: '+item['name'])
print('Verified',len(lock['files']),'CC0 inputs at pinned mirror/file revisions')
