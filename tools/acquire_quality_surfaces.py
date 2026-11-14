#!/usr/bin/env python3
"""Fetch exactly the pinned selected CC0 PBR inputs, with bounded verified bytes."""
import hashlib
import json
from pathlib import Path
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
lock=json.loads((ROOT/'data/quality-surface-lock.json').read_text())
for surface in lock['surfaces'].values():
    for item in surface['files']:
        p=ROOT/item['path']
        if not p.resolve().is_relative_to((ROOT/'assets/source/quality').resolve()):raise SystemExit('Unsafe surface path')
        if p.exists():raw=p.read_bytes()
        else:
            with urllib.request.urlopen(urllib.request.Request(item['url'],headers={'User-Agent':'EmeraldPrivateReconstruction/1.0'}),timeout=60) as response:raw=response.read(16*1024*1024+1)
        if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:raise SystemExit('Source surface mismatch; existing file preserved: '+p.name)
        p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():p.write_bytes(raw)
print('Verified nine selected CC0 2K PBR inputs')
