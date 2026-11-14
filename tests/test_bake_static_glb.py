import json
from pathlib import Path
import struct
import tempfile
import unittest
import numpy as np
from tools.bake_static_glb import bake,load,accessor


def fixture(path,nodes,roots,animations=None):
    points=np.array([[0,0,0],[1,0,0],[0,1,0]],dtype='<f4')
    normals=np.tile(np.array([1,1,0],dtype=float)/np.sqrt(2),(3,1)).astype('<f4')
    indices=np.array([[0],[1],[2]],dtype='<u2')
    uv=np.array([[0,0],[1,0],[0,1]],dtype='<f4')
    binary=points.tobytes()+normals.tobytes()+indices.tobytes()+b'\0\0'+uv.tobytes()
    doc={'asset':{'version':'2.0'},'buffers':[{'byteLength':len(binary)}],
         'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':36},{'buffer':0,'byteOffset':36,'byteLength':36},
                        {'buffer':0,'byteOffset':72,'byteLength':6},{'buffer':0,'byteOffset':80,'byteLength':24}],
         'accessors':[{'bufferView':0,'componentType':5126,'count':3,'type':'VEC3'},
                      {'bufferView':1,'componentType':5126,'count':3,'type':'VEC3'},
                      {'bufferView':2,'componentType':5123,'count':3,'type':'SCALAR'},
                      {'bufferView':3,'componentType':5126,'count':3,'type':'VEC2'}],
         'materials':[{'name':'licensed_fixture_material'}],
         'meshes':[{'primitives':[{'attributes':{'POSITION':0,'NORMAL':1,'TEXCOORD_0':3},'indices':2,'material':0}]}],
         'nodes':nodes,'scenes':[{'nodes':roots}],'scene':0}
    if animations is not None:doc['animations']=animations
    text=json.dumps(doc).encode();text+=b' '*((-len(text))%4)
    path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(text)+len(binary))+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(binary),0x004e4942)+binary)

class CompleteSceneBake(unittest.TestCase):
    def test_every_scene_mesh_and_child_transform_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.glb';output=Path(folder)/'complete.glb'
            fixture(source,[{'translation':[10,0,0],'children':[1]},{'mesh':0,'translation':[0,2,0]},{'mesh':0,'translation':[0,0,3]}],[0,2])
            report=bake(source,output);doc,binary=load(output)
            self.assertEqual(report['source_mesh_instances'],2)
            self.assertEqual(len(doc['nodes']),1);self.assertEqual(len(doc['meshes']),1)
            p,q=doc['meshes'][0]['primitives']
            np.testing.assert_allclose(accessor(doc,binary,p['attributes']['POSITION']),[[10,2,0],[11,2,0],[10,3,0]])
            np.testing.assert_allclose(accessor(doc,binary,q['attributes']['POSITION']),[[0,0,3],[1,0,3],[0,1,3]])
            np.testing.assert_allclose(accessor(doc,binary,p['attributes']['TEXCOORD_0']),[[0,0],[1,0],[0,1]])
            self.assertEqual(p['material'],0);self.assertEqual(doc['materials'][0]['name'],'licensed_fixture_material')

    def test_mirrored_scale_reverses_winding_and_transforms_normals(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.glb';output=Path(folder)/'complete.glb'
            fixture(source,[{'mesh':0,'scale':[-2,1,1]}],[0])
            bake(source,output);doc,binary=load(output);p=doc['meshes'][0]['primitives'][0]
            self.assertEqual(accessor(doc,binary,p['indices']).ravel().tolist(),[0,2,1])
            np.testing.assert_allclose(accessor(doc,binary,p['attributes']['NORMAL']),np.tile(np.array([-.5,1,0])/np.sqrt(1.25),(3,1)),atol=1e-6)

    def test_animation_input_is_not_silently_frozen(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.glb';output=Path(folder)/'complete.glb'
            fixture(source,[{'mesh':0}],[0],animations=[{}])
            with self.assertRaisesRegex(ValueError,'animated/skinned'):bake(source,output)

    def test_real_bed_is_complete_not_just_the_first_pillow_asset(self):
        root=Path(__file__).resolve().parents[1]
        source=root/'.references/kenney/furniturekit_updated/Models/GLTF format/bedSingle.glb'
        if not source.exists():self.skipTest('Acquire pinned licensed base assets first')
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'bed.glb';report=bake(source,output);doc,binary=load(output)
            self.assertEqual(report['source_mesh_instances'],3)
            self.assertEqual(len(doc['meshes']),1)
            self.assertEqual(len(doc['meshes'][0]['primitives']),6)
            self.assertGreater(report['bounds_gltf']['max'][2]-report['bounds_gltf']['min'][2],.7)

if __name__=='__main__':unittest.main()
