#!/usr/bin/env python3
"""Prepare complete licensed-object variants; raw inputs stay unchanged."""
import copy,hashlib,json,math,shutil,sys
from pathlib import Path
import numpy as np
from pack_static_gltf import pack
from bake_static_glb import bake,load,accessor,transform
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'out/quality-pass/packed-furnishing-variants';out.mkdir(parents=True,exist_ok=True);rows=[]
book=next(a for a in json.loads((ROOT/'data/quality-fixture-lock.json').read_text())['assets'] if a['id']=='book_encyclopedia_set_01')
source=next(ROOT/f['path'] for f in book['source_files'] if f['path'].endswith('.gltf'));packed=out/'books.glb';pack(source,packed);doc,binary=load(packed);derivative=copy.deepcopy(doc);nodes=[];height=0.
for i in range(6):
    original=doc['nodes'][i];world=transform(original);points=np.concatenate([accessor(doc,binary,p['attributes']['POSITION']) for p in doc['meshes'][original['mesh']]['primitives']]);points=points@world[:3,:3].T+world[:3,3]
    a=math.pi/2;b=math.radians((-1 if i%2 else 1)*4);rz=np.array([[0,-1,0],[1,0,0],[0,0,1.]]);ry=np.array([[math.cos(b),0,math.sin(b)],[0,1,0],[-math.sin(b),0,math.cos(b)]]);rotation=ry@rz;q=points@rotation.T;lo=q.min(axis=0);hi=q.max(axis=0);shift=np.array([-(lo[0]+hi[0])/2,height-lo[1],-(lo[2]+hi[2])/2]);adjust=np.eye(4);adjust[:3,:3]=rotation;adjust[:3,3]=shift
    nodes.append({'name':'CompleteVolume_'+str(i+1),'mesh':original['mesh'],'matrix':(adjust@world).reshape(-1,order='F').tolist()});height+=hi[1]-lo[1]+.001
derivative['nodes']=nodes;derivative['scenes']=[{'nodes':list(range(6))}];derivative['scene']=0
# Store a complete packed staging document with unchanged source image/buffer payload.
import struct
def write_glb(doc,binary,path):
    text=json.dumps(doc,separators=(',',':')).encode();text+=b' '*((-len(text))%4);binary+=b'\0'*((-len(binary))%4);path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(text)+len(binary))+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(binary),0x004e4942)+binary)
stage=out/'book_stack.glb';write_glb(derivative,binary,stage);target=ROOT/'unreal/Emerald/Content/Imported/SourceModels/Fixture_book_stack.glb';result=bake(stage,target);result['triangles']=sum(doc['accessors'][p['indices']]['count']//3 for i in range(6) for p in doc['meshes'][doc['nodes'][i]['mesh']]['primitives'])
rows.append(dict(id='book_stack',name='Six complete encyclopedia volumes stacked',author=book['author'],url=book['url'],license='CC0-1.0',baked_file=str(target.relative_to(ROOT)),baked=result,texture_token='book_stack',source_files=[]))
for file in ('fab-computer-lock.json','fab-fridge-lock.json'):
    lock=json.loads((ROOT/'data'/file).read_text());source=ROOT/lock['source_file']
    if not source.exists():
        download=Path.home()/'Downloads'/source.name;source.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(download,source)
    if source.stat().st_size!=lock['bytes'] or hashlib.sha256(source.read_bytes()).hexdigest()!=lock['sha256']:raise SystemExit('Licensed furnishing source differs; preserved')
    doc,binary=load(source);name='fab_retrocomputer' if file=='fab-computer-lock.json' else 'fab_fridge'
    if name=='fab_fridge':
        if doc['nodes'][2].get('name')!='GLTF_SceneRootNode' or doc['nodes'][5].get('name')!='Fridge_3':raise SystemExit('Clean refrigerator variant hierarchy changed')
        doc['nodes'][2]['children']=[5] # Exclude display ground and weathered alternative; keep all clean object parts/ancestors.
        stage=out/'clean_fridge.glb';write_glb(doc,binary,stage)
    else:stage=source
    target=ROOT/'unreal/Emerald/Content/Imported/SourceModels'/('Fixture_'+name+'.glb');result=bake(stage,target)
    result['triangles']=8596 if name=='fab_fridge' else lock['baked']['triangles']
    rows.append(dict(id=name,name=lock['name'],author=lock['author'],url=lock['url'],license=lock['license'],baked_file=str(target.relative_to(ROOT)),baked=result,source_files=[]))
(ROOT/'data/furnishing-variants-report.json').write_text(json.dumps({'assets':rows,'scope':'Complete selected objects/clean variant; native geometry/PBR/facing/world fit requires inspection','quality_gate_passed':False},indent=2)+'\n');print('Prepared complete furnishing variants',[(r['id'],r['baked']['source_mesh_instances'],r['baked']['triangles']) for r in rows])
