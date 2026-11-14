#!/usr/bin/env python3
"""Stage the complete licensed skin, morph targets and texture payload unchanged."""
import json,hashlib,struct
from pathlib import Path
from bake_static_glb import load
from acquire_fab_characters import acquire
ROOT=Path(__file__).resolve().parents[1]
acquire()
item=json.loads((ROOT/'data/fab-character-quality-lock.json').read_text())['assets'][0]
source=ROOT/item['file']
if hashlib.sha256(source.read_bytes()).hexdigest()!=item['sha256']:raise SystemExit('Licensed character source differs; preserved')
doc,binary=load(source);original_names=[]
for i,animation in enumerate(doc.get('animations',[])):
    original_names.append(animation.get('name'));animation['name']='OriginalFaceTest_'+str(i+1)
# The source has duplicate facial-test names. Only names change in this
# derivative; no skin, bind matrices, morphs, geometry or motion keys are baked.
text=json.dumps(doc,separators=(',',':')).encode();text+=b' '*((-len(text))%4);binary+=b'\0'*((-len(binary))%4)
raw=struct.pack('<III',0x46546c67,2,28+len(text)+len(binary))+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(binary),0x004e4942)+binary
output=ROOT/'unreal/Emerald/Content/Imported/QualityCharacterSources/CartoonCuteGirl.glb';output.parent.mkdir(parents=True,exist_ok=True)
if not output.exists() or hashlib.sha256(output.read_bytes()).hexdigest()!=hashlib.sha256(raw).hexdigest():
    temporary=output.with_suffix('.tmp');temporary.write_bytes(raw);temporary.replace(output)
report={'name':item['name'],'source_sha256':item['sha256'],'staged_sha256':hashlib.sha256(raw).hexdigest(),'file':str(output.relative_to(ROOT)),'source_meshes':len(doc['meshes']),'source_skin_count':len(doc.get('skins',[])),'source_joint_names':[[doc['nodes'][j].get('name') for j in s['joints']] for s in doc.get('skins',[])],'source_triangles':sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives']),'material_count':len(doc['materials']),'image_count':len(doc['images']),'morph_primitive_count':sum(bool(p.get('targets')) for m in doc['meshes'] for p in m['primitives']),'original_animation_names':original_names,'staged_animation_names':[a['name'] for a in doc.get('animations',[])],'locomotion_included':False,'modification':'Unique names for four duplicate original facial-test animations only; complete original skin/morph/mesh/image/key payload retained','native_import_verified':False,'quality_gate_passed':False}
(ROOT/'data/quality-character-preparation-report.json').write_text(json.dumps(report,indent=2)+'\n');print('Prepared complete high-detail character candidate:',report['source_meshes'],'meshes,',len(report['source_joint_names'][0]),'joints,',report['source_triangles'],'triangles; locomotion retarget still required')
