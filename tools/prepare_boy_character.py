#!/usr/bin/env python3
"""Verify and stage the complete licensed boy rig without flattening its skin."""
import hashlib,json,shutil,struct,zipfile
from pathlib import Path
from bake_static_glb import load
ROOT=Path(__file__).resolve().parents[1];item=json.loads((ROOT/'data/fab-boy-character-lock.json').read_text())
archive=ROOT/item['archive'];source=archive if archive.exists() else Path.home()/'Downloads'/archive.name;target=ROOT/item['file']
raw=source.read_bytes()
if len(raw)!=item['archive_bytes'] or hashlib.sha256(raw).hexdigest()!=item['archive_sha256']:raise SystemExit('Licensed boy archive differs; preserved')
if not target.resolve().is_relative_to((ROOT/'assets/source/fab-characters').resolve()):raise SystemExit('Unexpected boy source path')
archive.parent.mkdir(parents=True,exist_ok=True)
if not archive.exists():shutil.copyfile(source,archive)
with zipfile.ZipFile(archive) as bundle:
    members=bundle.infolist()
    if len(members)!=1 or members[0].filename!=item['member'] or members[0].file_size!=item['bytes'] or members[0].file_size>128*1024*1024:raise SystemExit('Unexpected boy archive member')
    raw=bundle.read(members[0])
if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:raise SystemExit('Licensed boy GLB differs')
target.parent.mkdir(parents=True,exist_ok=True)
if target.exists() and target.read_bytes()!=raw:raise SystemExit('Existing boy input differs; preserved')
if not target.exists():target.write_bytes(raw)
doc,binary=load(target);names=[]
for i,a in enumerate(doc.get('animations',[])):names.append(a.get('name'));a['name']='OriginalFaceTest_'+str(i+1)
text=json.dumps(doc,separators=(',',':')).encode();text+=b' '*((-len(text))%4);binary+=b'\0'*((-len(binary))%4)
raw=struct.pack('<III',0x46546c67,2,28+len(text)+len(binary))+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(binary),0x004e4942)+binary
output=ROOT/'unreal/Emerald/Content/Imported/QualityCharacterSources/CartoonYoungBoy.glb';output.parent.mkdir(parents=True,exist_ok=True);temporary=output.with_suffix('.tmp');temporary.write_bytes(raw);temporary.replace(output)
report={'name':item['name'],'source_sha256':item['sha256'],'staged_sha256':hashlib.sha256(raw).hexdigest(),'file':str(output.relative_to(ROOT)),'source_meshes':len(doc['meshes']),'source_skin_count':len(doc.get('skins',[])),'source_joint_names':[[doc['nodes'][j].get('name') for j in s['joints']] for s in doc.get('skins',[])],'source_triangles':sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives']),'material_count':len(doc['materials']),'image_count':len(doc['images']),'morph_primitive_count':sum(bool(p.get('targets')) for m in doc['meshes'] for p in m['primitives']),'original_animation_names':names,'staged_animation_names':[a['name'] for a in doc.get('animations',[])],'locomotion_included':False,'modification':'Unique names for seven duplicate original facial-test clips only; all original skin/binds/morphs/geometry/images/keys preserved','native_import_verified':False,'quality_gate_passed':False}
assert report['source_meshes']==11 and len(report['source_joint_names'][0])==555 and report['source_triangles']==91005
(ROOT/'data/boy-character-preparation-report.json').write_text(json.dumps(report,indent=2)+'\n');print('Prepared complete11-part/555-joint licensed boy; no body motion authored')
