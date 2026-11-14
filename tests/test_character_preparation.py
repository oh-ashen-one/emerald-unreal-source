import base64
import copy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from tools.pack_static_gltf import pack
from tools.bake_static_glb import load,accessor,bake

ROOT=Path(__file__).resolve().parents[1]
class CharacterRigPreservation(unittest.TestCase):
    def test_embedded_rig_weights_and_animation_keys_survive_container_pack(self):
        path=ROOT/'assets/source/quaternius-characters/Doctor_Male_Young.gltf'
        if not path.exists():self.skipTest('Acquire selected licensed character first')
        source=json.loads(path.read_text());binary=base64.b64decode(source['buffers'][0]['uri'].split(',',1)[1])
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'model.glb';pack(path,target);doc,data=load(target)
            self.assertEqual(doc['skins'],source['skins']);self.assertEqual(doc['animations'],source['animations'])
            self.assertEqual(doc['nodes'],source['nodes'])
            for mesh in source['meshes']:
                for primitive in mesh['primitives']:
                    for key in ('POSITION','JOINTS_0','WEIGHTS_0'):
                        index=primitive['attributes'][key]
                        np.testing.assert_array_equal(accessor(source,binary,index),accessor(doc,data,index))
            for anim in source['animations']:
                for sampler in anim['samplers']:
                    for key in ('input','output'):
                        index=sampler[key];np.testing.assert_array_equal(accessor(source,binary,index),accessor(doc,data,index))
            with self.assertRaisesRegex(ValueError,'animated/skinned'):bake(target,Path(temp)/'invalid.glb')

    def test_bounded_embedded_payload_is_validated(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for uri in ('data:application/octet-stream;base64,not valid','data:text/html;base64,AAAA'):
                p=root/'bad.gltf';p.write_text(json.dumps({'asset':{'version':'2.0'},'buffers':[{'uri':uri,'byteLength':3}]}))
                with self.assertRaises((ValueError,base64.binascii.Error)):pack(p,root/'bad.glb')
                self.assertFalse((root/'bad.glb').exists())

    def test_roles_preserve_original_graphics_constants_and_palette_indices(self):
        plan=json.loads((ROOT/'data/character-role-plan.json').read_text());program=json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/source-events.json').read_text())
        self.assertEqual(plan['graphics'][str(program['constants']['OBJ_EVENT_GFX_MOM'])],'mom')
        self.assertEqual(plan['graphics'][str(program['constants']['OBJ_EVENT_GFX_PROF_BIRCH'])],'birch')
        from PIL import Image
        for p in plan['profiles'].values():
            image=Image.open(ROOT/p['source_sprite']);palette=image.getpalette()
            for name,index in p['palette_indices'].items():self.assertEqual(p['colors_rgb8'][name],palette[index*3:index*3+3])
            self.assertGreater(p['height_cm'],0)
