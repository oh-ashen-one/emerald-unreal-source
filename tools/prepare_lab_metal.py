#!/usr/bin/env python3
"""Verify or restore only the pinned public CC0 scan dependencies."""
import json,hashlib,urllib.request
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
for f in json.loads((ROOT/'data/lab-metal-lock.json').read_text())['files']:
    path=(ROOT/f['path']).resolve()
    if not path.is_relative_to((ROOT/'assets/source/lab-metal').resolve()) or urlparse(f['url']).hostname!='dl.polyhaven.org':raise SystemExit('Unexpected lab surface source')
    if path.exists():raw=path.read_bytes()
    else:
        with urllib.request.urlopen(urllib.request.Request(f['url'],headers={'User-Agent':'EmeraldPrivateReconstruction/1.0'}),timeout=60) as r:raw=r.read(32*1024*1024+1)
    if len(raw)!=f['bytes'] or hashlib.sha256(raw).hexdigest()!=f['sha256']:raise SystemExit('Lab metal input differs; preserved')
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():path.write_bytes(raw)
print('Verified original scanned lab surface maps')
