#!/usr/bin/env python3
"""Verify a free Fab archive and retain complete LOD0 variants separately."""
import copy,hashlib,json,shutil,zipfile
from pathlib import Path
from pack_static_gltf import pack
from bake_static_glb import bake
ROOT=Path(__file__).resolve().parents[1]
lock=json.loads((ROOT/'data/fab-grass-lock.json').read_text())
archive=ROOT/lock['archive'];source=archive if archive.exists() else Path.home()/'Downloads'/archive.name
raw=source.read_bytes()
if len(raw)!=lock['archive_bytes'] or hashlib.sha256(raw).hexdigest()!=lock['archive_sha256']:raise SystemExit('Grass archive differs; preserved')
archive.parent.mkdir(parents=True,exist_ok=True)
if not archive.exists():shutil.copyfile(source,archive)
base=ROOT/'assets/source/quality-grass';base.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive) as z:
    expected={f['member']:f for f in lock['files']}
    if {i.filename for i in z.infolist() if not i.is_dir()}!=set(expected):raise SystemExit('Unexpected grass archive members')
    for name,f in expected.items():
        p=(base/name).resolve()
        if not p.is_relative_to(base.resolve()) or f['bytes']>64*1024*1024:raise SystemExit('Unsafe grass dependency')
        raw=z.read(name)
        if len(raw)!=f['bytes'] or hashlib.sha256(raw).hexdigest()!=f['sha256']:raise SystemExit('Grass dependency differs')
        if p.exists() and p.read_bytes()!=raw:raise SystemExit('Existing grass input differs; preserved')
        p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():p.write_bytes(raw)
doc=json.loads((base/'wiljearqx_tier_1.gltf').read_text());rows=[]
for i,letter in enumerate('ABCDEFGH'):
    index=i*4;d=copy.deepcopy(doc)
    assert d['nodes'][index]['name']=='SM_wiljearqx_Var'+letter
    selected=copy.deepcopy(d['nodes'][index]);selected['mesh']=0
    d['nodes']=[selected];d['meshes']=[d['meshes'][index]];d['scenes']=[{'nodes':[0]}];d['scene']=0
    # Use the publisher's standard non-UE opacity/color variant. ORT is not
    # metallic: R=opacity, G=roughness, B=translucency; native shader binds it.
    d['materials']=d['materials'][:1];d['materials'][0]['alphaMode']='MASK';d['materials'][0]['pbrMetallicRoughness']['metallicFactor']=0
    d['images']=d['images'][:3];d['images'][2]['uri']='Textures/T_wiljearqx_4K_B-O.png';d['textures']=d['textures'][:3]
    prepared=base/('Grass'+letter+'.gltf');prepared.write_text(json.dumps(d,separators=(',',':')))
    packed=ROOT/'out/quality-pass/packed-grass'/('Grass'+letter+'.glb');pack(prepared,packed)
    output=ROOT/'unreal/Emerald/Content/Imported/SourceModels'/('QualityGrass'+letter+'.glb');result=bake(packed,output)
    triangles=sum(doc['accessors'][p['indices']]['count']//3 for p in doc['meshes'][index]['primitives'])
    rows.append(dict(name='QualityGrass'+letter,path=str(output.relative_to(ROOT)),triangles=triangles,**result))
(ROOT/'data/quality-grass-preparation-report.json').write_text(json.dumps(dict(variants=rows,source=lock['url'],license=lock['license'],scope='Each complete source LOD0 variant baked independently with source transform. Other LODs retained in original package, not overlaid or claimed as installed.'),indent=2)+'\n')
print('Prepared8 complete source grass variants; original archive unchanged')
