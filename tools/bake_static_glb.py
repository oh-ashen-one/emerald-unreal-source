#!/usr/bin/env python3
"""Bake every static scene node into one mesh, preserving materials and attributes.

A glTF file can have many meshes/nodes. Importing its first native StaticMesh is
not a complete model. Output has one identity node/mesh with all scene primitives.
Original licensed inputs stay unmodified. Skinning/morphs/animations are rejected.
"""
import copy
import hashlib
import json
from pathlib import Path
import struct
import numpy as np

_DTYPES={5120:'<i1',5121:'<u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}
_WIDTHS={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}


def load(path):
    raw=Path(path).read_bytes()
    magic,version,total=struct.unpack_from('<III',raw)
    if magic!=0x46546c67 or version!=2 or total!=len(raw): raise ValueError('Invalid GLB2')
    offset=12;doc=None;binary=b''
    while offset<len(raw):
        size,kind=struct.unpack_from('<II',raw,offset);chunk=raw[offset+8:offset+8+size];offset+=8+size
        if kind==0x4e4f534a:doc=json.loads(chunk)
        elif kind==0x004e4942:binary=chunk
    if doc is None:raise ValueError('Missing JSON chunk')
    return doc,binary


def accessor(doc,binary,index):
    a=doc['accessors'][index]
    if 'sparse' in a:raise ValueError('Sparse accessor needs explicit support')
    v=doc['bufferViews'][a['bufferView']]
    if v.get('buffer',0)!=0:raise ValueError('External geometry buffer')
    dtype=np.dtype(_DTYPES[a['componentType']]);width=_WIDTHS[a['type']]
    stride=v.get('byteStride',dtype.itemsize*width)
    return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,
                      offset=v.get('byteOffset',0)+a.get('byteOffset',0),
                      strides=(stride,dtype.itemsize)).copy()


def transform(node):
    if 'matrix' in node:return np.array(node['matrix'],dtype=float).reshape(4,4,order='F')
    x,y,z,w=node.get('rotation',[0,0,0,1])
    r=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    m=np.eye(4);m[:3,:3]=r@np.diag(node.get('scale',[1,1,1]));m[:3,3]=node.get('translation',[0,0,0])
    return m


def bake(source,destination):
    original,binary=load(source)
    if original.get('animations') or original.get('skins'):raise ValueError('Static conversion rejects animated/skinned input')
    doc=copy.deepcopy(original);payload=bytearray(binary);primitives=[];instances=0;vertex_count=0;all_positions=[]
    def append(values,kind,component=5126,target=34962):
        while len(payload)%4:payload.append(0)
        dtype=np.dtype(_DTYPES[component]);values=np.asarray(values,dtype=dtype)
        offset=len(payload);raw=values.tobytes();payload.extend(raw)
        view=len(doc.setdefault('bufferViews',[]));doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(raw),'target':target})
        record={'bufferView':view,'componentType':component,'count':len(values),'type':kind}
        if kind in ('VEC3','SCALAR'):
            record['min']=values.min(axis=0).astype(float if component==5126 else int).tolist()
            record['max']=values.max(axis=0).astype(float if component==5126 else int).tolist()
        index=len(doc.setdefault('accessors',[]));doc['accessors'].append(record);return index
    def visit(index,parent,chain):
        nonlocal instances,vertex_count
        if index in chain:raise ValueError('Cyclic node hierarchy')
        node=original['nodes'][index]
        if 'skin' in node:raise ValueError('Skinned node')
        world=parent@transform(node)
        if not np.isfinite(world).all():raise ValueError('Non-finite node transform')
        if 'mesh' in node:
            instances+=1
            linear=world[:3,:3];det=np.linalg.det(linear)
            if abs(det)<1e-12:raise ValueError('Singular node transform')
            normal_matrix=np.linalg.inv(linear).T
            for source_primitive in original['meshes'][node['mesh']]['primitives']:
                if source_primitive.get('targets'):raise ValueError('Morph target input')
                if source_primitive.get('mode',4)!=4:raise ValueError('Non-triangle primitive')
                primitive=copy.deepcopy(source_primitive);attrs=primitive['attributes']
                positions=accessor(original,binary,attrs['POSITION']).astype(float)
                positions=positions@linear.T+world[:3,3]
                if not np.isfinite(positions).all():raise ValueError('Non-finite geometry')
                attrs['POSITION']=append(positions,'VEC3');vertex_count+=len(positions);all_positions.append(positions)
                if 'NORMAL' in attrs:
                    normals=accessor(original,binary,attrs['NORMAL'])@normal_matrix.T
                    normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-15)
                    attrs['NORMAL']=append(normals,'VEC3')
                if 'TANGENT' in attrs:
                    tangents=accessor(original,binary,attrs['TANGENT']).astype(float)
                    directions=tangents[:,:3]@linear.T
                    if 'NORMAL' in attrs:directions-=normals*np.sum(directions*normals,axis=1,keepdims=True)
                    directions/=np.maximum(np.linalg.norm(directions,axis=1,keepdims=True),1e-15)
                    tangents[:,:3]=directions;tangents[:,3]*=1 if det>0 else -1
                    attrs['TANGENT']=append(tangents,'VEC4')
                if det<0:
                    indices=accessor(original,binary,primitive['indices']).reshape(-1,3).copy() if 'indices' in primitive else np.arange(len(positions)).reshape(-1,3)
                    indices[:,[1,2]]=indices[:,[2,1]]
                    primitive['indices']=append(indices.reshape(-1,1),'SCALAR',5125,34963)
                primitives.append(primitive)
        for child in node.get('children',[]):visit(child,world,chain|{index})
    for root in original['scenes'][original.get('scene',0)]['nodes']:visit(root,np.eye(4),set())
    if not primitives:raise ValueError('Scene contains no geometry')
    points=np.concatenate(all_positions)
    name=Path(source).stem+'_Complete'
    doc['nodes']=[{'name':name,'mesh':0}];doc['meshes']=[{'name':name,'primitives':primitives}]
    doc['scenes']=[{'name':name,'nodes':[0]}];doc['scene']=0
    doc['buffers']=[{'byteLength':len(payload)}]
    doc.setdefault('extras',{})['emerald_conversion']={'schema':'static-scene-bake/1','source_sha256':hashlib.sha256(Path(source).read_bytes()).hexdigest(),'source_mesh_instances':instances}
    text=json.dumps(doc,separators=(',',':')).encode()
    text+=b' '*((-len(text))%4);payload.extend(b'\0'*((-len(payload))%4))
    total=12+8+len(text)+8+len(payload)
    output=struct.pack('<III',0x46546c67,2,total)+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(payload),0x004e4942)+payload
    Path(destination).parent.mkdir(parents=True,exist_ok=True);Path(destination).write_bytes(output)
    return {'source_mesh_instances':instances,'source_nodes':len(original['nodes']),'output_meshes':1,'primitives':len(primitives),'vertices':vertex_count,
            'bounds_gltf':{'min':points.min(axis=0).tolist(),'max':points.max(axis=0).tolist()},'sha256':hashlib.sha256(output).hexdigest()}


if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];lock=json.loads((root/'data/asset-lock.json').read_text());report={}
    for item in lock['files']:
        source=root/item['path'];output=root/'unreal/Emerald/Content/Imported/SourceModels'/(item['name']+'_Complete.glb')
        if hashlib.sha256(source.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Pinned source asset changed: '+item['name'])
        report[item['name']]=bake(source,output)
    (root/'data/art-bake-report.json').write_text(json.dumps({'schema':'static-scene-bake/1','models':report},indent=2)+'\n')
    print('Baked complete static assemblies:',len(report),'bed source mesh instances:',report['bedSingle']['source_mesh_instances'])
