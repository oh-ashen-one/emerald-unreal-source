#!/usr/bin/env python3
"""Fetch only the pinned CC0 texture/HDR inputs, then verify their bytes."""
import hashlib
import json
from pathlib import Path
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
lock=json.loads((ROOT/'data/pbr-lock.json').read_text())
files=lock['files']+[lock['environment']]+json.loads((ROOT/'data/exterior-surface-lock.json').read_text())['files']
for item in files:
    path=ROOT/item['path']
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        request=urllib.request.Request(item['url'],headers={'User-Agent':'EmeraldPrivateReconstruction/1.0'})
        with urllib.request.urlopen(request,timeout=60) as response:
            data=response.read(32*1024*1024)
        if hashlib.sha256(data).hexdigest()!=item['sha256']:
            raise SystemExit('Downloaded surface hash mismatch: '+path.name)
        path.write_bytes(data)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
        raise SystemExit('Existing surface differs; preserved: '+path.name)
print('Verified',len(files),'pinned CC0 surface/environment files')
