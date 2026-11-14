#!/usr/bin/env python3
"""Acquire pinned CC0 model dependencies and bake the complete static scene."""
import hashlib,json,urllib.request
from pathlib import Path
from urllib.parse import urlparse
from pack_static_gltf import pack
from bake_static_glb import bake
ROOT=Path(__file__).resolve().parents[1]
for item in json.loads((ROOT/'data/quality-furniture-lock.json').read_text())['assets']:
    source=None
    for f in item['source_files']:
        path=(ROOT/f['path']).resolve()
        if not path.is_relative_to((ROOT/'assets/source/quality-furniture').resolve()):raise SystemExit('Unsafe furniture path')
        if urlparse(f['url']).hostname!='dl.polyhaven.org':raise SystemExit('Unexpected source host')
        if path.exists():raw=path.read_bytes()
        else:
            with urllib.request.urlopen(urllib.request.Request(f['url'],headers={'User-Agent':'EmeraldPrivateReconstruction/1.0'}),timeout=60) as response:raw=response.read(16*1024*1024+1)
        if len(raw)!=f['bytes'] or hashlib.sha256(raw).hexdigest()!=f['sha256']:raise SystemExit('Furniture source mismatch; preserved')
        path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():path.write_bytes(raw)
        if path.suffix=='.gltf':source=path
    if source is None:raise SystemExit('Missing static source document')
    target=ROOT/item['baked_file']
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest()!=item['baked']['sha256']:raise SystemExit('Existing furniture derivative differs; preserved')
    else:
        packed=ROOT/'out/quality-pass/packed-furniture'/(item['id']+'.glb');pack(source,packed)
        temporary=packed.with_name(item['id']+'-baked.glb');report=bake(packed,temporary)
        if report['sha256']!=item['baked']['sha256']:raise SystemExit('Furniture bake differs from pinned complete scene')
        target.parent.mkdir(parents=True,exist_ok=True);temporary.replace(target)
print('Verified and complete-scene baked four licensed CC0 furnishing models')
for f in json.loads((ROOT/'data/quality-textile-lock.json').read_text())['files']:
    path=(ROOT/f['path']).resolve()
    if not path.is_relative_to((ROOT/'assets/source/quality-textile').resolve()) or urlparse(f['url']).hostname!='dl.polyhaven.org':raise SystemExit('Unexpected textile source')
    if path.exists():raw=path.read_bytes()
    else:
        with urllib.request.urlopen(urllib.request.Request(f['url'],headers={'User-Agent':'EmeraldPrivateReconstruction/1.0'}),timeout=60) as response:raw=response.read(16*1024*1024+1)
    if len(raw)!=f['bytes'] or hashlib.sha256(raw).hexdigest()!=f['sha256']:raise SystemExit('Textile source mismatch; preserved')
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():path.write_bytes(raw)
print('Verified three licensed textile maps')
