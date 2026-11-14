"""Preserve licensed skin/rig/keys; select existing clips and embed GLB data."""
import base64
import hashlib
import json
from pathlib import Path
from pack_static_gltf import pack
from bake_static_glb import accessor

ROOT=Path(__file__).resolve().parents[1]

def prepare(item):
    source=ROOT/item['path']
    if hashlib.sha256(source.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Character source changed: '+item['name'])
    doc=json.loads(source.read_text());binary=base64.b64decode(doc['buffers'][0]['uri'].split(',',1)[1],validate=True)
    if len(doc['buffers'])!=1 or len(doc.get('skins',[]))!=1:raise ValueError('Inspect changed rig structure')
    parents={c:i for i,n in enumerate(doc['nodes']) for c in n.get('children',[])};joints=set(doc['skins'][0]['joints']);roots={i for i in joints if parents.get(i) not in joints}
    animations={a['name']:a for a in doc['animations']};chosen=[];clip_info={};aliases={}
    for name in ('Idle','Walk','Run','SitDown'):
        source_name=name if name in animations else ('Walk' if name=='Run' else name)
        aliases[name]=source_name;a=animations[source_name];duration=0.;root_range=[]
        for ch in a['channels']:
            sampler=a['samplers'][ch['sampler']];times=accessor(doc,binary,sampler['input']);duration=max(duration,float(times.max()))
            if ch['target']['node'] in roots and ch['target']['path']=='translation':
                data=accessor(doc,binary,sampler['output']);extent=data.max(axis=0)-data.min(axis=0);root_range.append(extent.tolist())
                if max(float(extent[0]),float(extent[2]))>1e-5:raise ValueError('Horizontal root motion needs explicit adaptation: '+name)
        clip_info[source_name]={'duration_s':duration,'root_translation_range_gltf':root_range}
        if a not in chosen:chosen.append(a)
    doc['animations']=chosen
    directory=ROOT/'unreal/Emerald/Content/Imported/CharacterSources';directory.mkdir(parents=True,exist_ok=True)
    stage=directory/(item['name']+'.gltf');stage.write_text(json.dumps(doc,separators=(',',':')))
    output=directory/(item['name']+'.glb');pack(stage,output);stage.unlink()
    return {'source_sha256':item['sha256'],'staged_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'path':str(output.relative_to(ROOT)),'source_clip_count':len(animations),'selected_clips':clip_info,'animation_aliases':aliases,'joint_names':[doc['nodes'][i]['name'] for i in doc['skins'][0]['joints']],'source_mesh_instances':sum('mesh' in n for n in doc['nodes']),'triangles':sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives']),'materials':{m['name']:m.get('pbrMetallicRoughness',{}).get('baseColorFactor',[1,1,1,1]) for m in doc['materials']}}

if __name__=='__main__':
    lock=json.loads((ROOT/'data/character-lock.json').read_text());result={i['name']:prepare(i) for i in lock['files']}
    (ROOT/'data/character-preparation-report.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Prepared',len(result),'rigged assemblies; only existing Idle/Walk/Run selected, no static bake')
