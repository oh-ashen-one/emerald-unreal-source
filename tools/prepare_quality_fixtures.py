#!/usr/bin/env python3
"""Restore pinned CC0 complete static fixtures without executing asset code."""
import hashlib,json,urllib.request
from pathlib import Path
from urllib.parse import urlparse
from pack_static_gltf import pack
from bake_static_glb import bake
ROOT=Path(__file__).resolve().parents[1]
for item in json.loads((ROOT/'data/quality-fixture-lock.json').read_text())['assets']:
    source=None
    for f in item['source_files']:
        path=(ROOT/f['path']).resolve()
        if not path.is_relative_to((ROOT/'assets/source/quality-fixtures').resolve()) or urlparse(f['url']).hostname!='dl.polyhaven.org':raise SystemExit('Unexpected fixture source')
        if path.exists():raw=path.read_bytes()
        else:
            with urllib.request.urlopen(urllib.request.Request(f['url'],headers={'User-Agent':'EmeraldPrivateReconstruction/1.0'}),timeout=60) as r:raw=r.read(32*1024*1024+1)
        if len(raw)!=f['bytes'] or hashlib.sha256(raw).hexdigest()!=f['sha256']:raise SystemExit('Fixture source differs; preserved')
        path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():path.write_bytes(raw)
        if path.suffix=='.gltf':source=path
    target=ROOT/item['baked_file']
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest()!=item['baked']['sha256']:raise SystemExit('Fixture derivative differs; preserved')
    else:
        temporary=ROOT/'out/quality-pass/packed-fixtures'/(item['id']+'.glb');pack(source,temporary)
        result=bake(temporary,target)
        if result['sha256']!=item['baked']['sha256']:raise SystemExit('Complete fixture scene bake differs')
print('Verified complete pinned CC0 fixture inputs, including all source parts and real4K maps')
