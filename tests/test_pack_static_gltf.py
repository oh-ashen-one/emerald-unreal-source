import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
import numpy as np
from test_bake_static_glb import fixture
from tools.bake_static_glb import load, accessor, bake
from tools.pack_static_gltf import pack


class SelectedGLTFPackaging(unittest.TestCase):
    def test_external_buffers_and_texture_survive_pack_and_scene_bake(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);fixture(root/'original.glb',[{'mesh':0}],[0])
            original,binary=load(root/'original.glb')
            doc=json.loads(json.dumps(original))
            (root/'first buffer.bin').write_bytes(binary[:72]);(root/'second.bin').write_bytes(binary[72:])
            doc['buffers']=[{'uri':'first%20buffer.bin','byteLength':72},{'uri':'second.bin','byteLength':len(binary)-72}]
            for view in doc['bufferViews'][2:]:view['buffer']=1;view['byteOffset']-=72
            (root/'textures').mkdir();Image.new('RGB',(2,2),(21,75,192)).save(root/'textures/color.png')
            doc['images']=[{'uri':'textures/color.png'}];doc['textures']=[{'source':0}]
            doc['materials'][0]['pbrMetallicRoughness']={'baseColorTexture':{'index':0}}
            (root/'model.gltf').write_text(json.dumps(doc))
            pack(root/'model.gltf',root/'packed.glb');bake(root/'packed.glb',root/'complete.glb')
            result,data=load(root/'complete.glb')
            for key in ('POSITION','NORMAL','TEXCOORD_0'):
                old=original['meshes'][0]['primitives'][0]['attributes'][key]
                new=result['meshes'][0]['primitives'][0]['attributes'][key]
                np.testing.assert_allclose(accessor(original,binary,old),accessor(result,data,new),atol=1e-6)
            view=result['bufferViews'][result['images'][0]['bufferView']]
            self.assertEqual(data[view['byteOffset']:view['byteOffset']+view['byteLength']],(root/'textures/color.png').read_bytes())
            self.assertEqual(result['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index'],0)

    def test_uri_schemes_path_escapes_and_wrong_lengths_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'buffer.bin').write_bytes(b'abcd')
            for uri,length in [('https://example.invalid/data',4),('../outside',4),('buffer.bin',5),('%2e%2e/outside',4),('https%3A%2F%2Fexample.invalid/data',4),('%5Coutside.bin',4)]:
                (root/'bad.gltf').write_text(json.dumps({'asset':{'version':'2.0'},'buffers':[{'uri':uri,'byteLength':length}]}))
                with self.assertRaises(ValueError):pack(root/'bad.gltf',root/'bad.glb')
                self.assertFalse((root/'bad.glb').exists())
