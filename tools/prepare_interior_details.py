#!/usr/bin/env python3
"""Prepare complete licensed sink/stair variants; preserve original archives."""
import copy,hashlib,json,shutil,zipfile
from pathlib import Path
from PIL import Image
from pack_static_gltf import pack
from bake_static_glb import bake,load

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out/quality-pass/packed-interior-details';OUT.mkdir(parents=True,exist_ok=True)

def restore(record,directory):
    archive=ROOT/record.get('source_archive',record.get('path',''))
    if len(archive.read_bytes())!=record['bytes'] or hashlib.sha256(archive.read_bytes()).hexdigest()!=record['sha256']:
        raise RuntimeError('Licensed detail archive differs; preserved')
    directory.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as package:
        for item in package.infolist():
            destination=(directory/item.filename).resolve()
            if not destination.is_relative_to(directory.resolve()) or item.file_size>32*1024*1024 or (item.external_attr>>16)&0o170000==0o120000:
                raise RuntimeError('Unsafe detail archive member')
            if item.is_dir():destination.mkdir(parents=True,exist_ok=True);continue
            raw=package.read(item);destination.parent.mkdir(parents=True,exist_ok=True)
            if destination.exists() and destination.read_bytes()!=raw:raise RuntimeError('Extracted source differs; preserved')
            if not destination.exists():destination.write_bytes(raw)

def baked_row(lock,name,source,selection):
    stage=OUT/(name+'.glb');pack(source,stage)
    target=ROOT/'unreal/Emerald/Content/Imported/SourceModels'/('Fixture_'+name+'.glb')
    result=bake(stage,target);doc,_=load(target)
    result['triangles']=sum(doc['accessors'][p['indices']]['count']//3 for mesh in doc['meshes'] for p in mesh['primitives'])
    return dict(id=name,name=lock['name'],author=lock['author'],url=lock['url'],license=lock['license'],baked_file=str(target.relative_to(ROOT)),baked=result,source_files=[],selection=selection)

sink=json.loads((ROOT/'data/fab-sink-lock.json').read_text());sink_folder=ROOT/'assets/source/fab-sink/original';restore(sink,sink_folder)
sink_stage=OUT/'sink';sink_stage.mkdir(exist_ok=True)
doc=json.loads((sink_folder/'scene.gltf').read_text());line_meshes=[]
for index,mesh in enumerate(doc['meshes']):
    modes={p.get('mode',4) for p in mesh['primitives']}
    if modes=={1}:line_meshes.append(index)
    elif modes!={4}:raise RuntimeError('Unhandled sink primitive type')
if line_meshes!=[38,39,40]:raise RuntimeError('Sink line-only source meshes changed')
for node in doc['nodes']:
    if node.get('mesh') in line_meshes:del node['mesh']
shutil.copyfile(sink_folder/'scene.bin',sink_stage/'scene.bin')
shutil.copytree(sink_folder/'textures',sink_stage/'textures',dirs_exist_ok=True)
(sink_stage/'sink.gltf').write_text(json.dumps(doc,indent=2)+'\n')
rows=[baked_row(sink,'fab_sink',sink_stage/'sink.gltf','Every triangle-surface part of cabinet/basin/tap/fittings retained; three line-only meshes38/39/40 (46line segments) are explicitly excluded from triangle-only native StaticMesh conversion; raw source unchanged')]

stairs=json.loads((ROOT/'data/fab-stairs-lock.json').read_text());folder=ROOT/'assets/source/fab-stairs';restore(stairs,folder/'original');restore(stairs['texture_archive'],folder/'textures')
source=folder/'original/Stairs Pack.gltf';doc=json.loads(source.read_text())
if doc['nodes'][4]['name']!='Cube.043' or doc['nodes'][24]['name']!='Cube.023' or len(doc['nodes'][24]['children'])!=8:
    raise RuntimeError('Straight complete stair hierarchy changed')
# One full straight staircase consists of its stone treads plus the colocated
# wood/rail assembly and all eight children. Other independent variants stay raw.
doc['scenes']=[{'nodes':[4,24]}];doc['scene']=0
stage=OUT/'stairs';stage.mkdir(exist_ok=True)
shutil.copyfile(folder/'original/Stairs Pack.bin',stage/'Stairs Pack.bin')
doc['images']=[];doc['textures']=[]
def texture(file):
    index=len(doc['images']);doc['images'].append({'uri':file});doc['textures'].append({'source':index});return {'index':index}
for index,label in [(0,'Wood 1'),(2,'White Tiles')]:
    color=label+(' Base color.png' if index==0 else ' Basecolor.png');normal=label+' Normal.png';rough=label+' Roughness.png'
    for file in (color,normal):shutil.copyfile(folder/'textures'/file,stage/file)
    image=Image.open(folder/'textures'/rough).convert('L');packed=label+' ARM.png'
    Image.merge('RGB',(Image.new('L',image.size,255),image,Image.new('L',image.size,0))).save(stage/packed)
    material=doc['materials'][index];pbr=material['pbrMetallicRoughness'];pbr.update(baseColorTexture=texture(color),metallicRoughnessTexture=texture(packed),metallicFactor=0,roughnessFactor=1)
    material['normalTexture']=texture(normal)
(stage/'stairs.gltf').write_text(json.dumps(doc,indent=2)+'\n')
rows.append(baked_row(stairs,'fab_stairs',stage/'stairs.gltf','Complete straight variant roots4+24 and all8children; supplied wood/stone color/normal/roughness maps reattached; roughness packed into G, metallic0, AO1'))
(ROOT/'data/interior-detail-report.json').write_text(json.dumps({'assets':rows,'quality_gate_passed':False,'scope':'Complete source preparation only; native geometry/PBR/facing/world and creator credits require verification'},indent=2)+'\n')
print('Prepared complete licensed interior details',[(r['id'],r['baked']['source_mesh_instances'],r['baked']['triangles']) for r in rows])
