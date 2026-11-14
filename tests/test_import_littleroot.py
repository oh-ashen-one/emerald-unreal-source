"""Differential checks against raw pret files, not golden importer snapshots."""
import hashlib
import json
from pathlib import Path
import struct
import unittest
from tools.import_littleroot import Importer, MAP_NAMES, unpack_block, words

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'pokeemerald'

class BlockContract(unittest.TestCase):
    def test_all_u16_words_roundtrip(self):
        for word in range(65536):
            c = unpack_block(word)
            self.assertEqual(word, c['metatile_id'] | c['collision'] << 10 | c['elevation'] << 12)

    def test_malformed_binary_rejected(self):
        with self.assertRaises(ValueError):
            words(b'\x00')
        with self.assertRaises(ValueError):
            unpack_block(65536)

@unittest.skipUnless((SOURCE/'data/layouts/layouts.json').is_file(), 'Clone pret/pokeemerald first')
class SourceDifferential(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = Importer(SOURCE).run()
        cls.maps = {m['id']: m for m in cls.data['maps']}

    def test_exact_scope_and_event_records(self):
        self.assertEqual(tuple(m['name'] for m in self.data['maps']), MAP_NAMES)
        for m in self.data['maps']:
            raw = json.loads((SOURCE/'data/maps'/m['name']/'map.json').read_text())
            self.assertEqual({k:v for k,v in m.items() if k != 'geometry'}, raw)

    def test_every_block_byte_and_geometry(self):
        for m in self.data['maps']:
            g = m['geometry']
            raw = (SOURCE/g['blockdata_filepath']).read_bytes()
            encoded = b''.join(struct.pack('<H', c['source_word']) for c in g['cells'])
            self.assertEqual(encoded, raw)
            for i,c in enumerate(g['cells']):
                lo,hi = raw[i*2:i*2+2]
                self.assertEqual(c['metatile_id'], lo + ((hi & 3) * 256))
                self.assertEqual(c['collision'], (hi // 4) % 4)
                self.assertEqual(c['elevation'], hi // 16)
                self.assertEqual(c['ue_center_cm'], [(i % g['width'])*200,(i//g['width'])*200,0])

    def test_tileset_words_and_attributes(self):
        for t in self.data['tilesets'].values():
            raw = (SOURCE/t['metatile_path']).read_bytes()
            attrs = (SOURCE/t['attribute_path']).read_bytes()
            self.assertEqual(raw, b''.join(struct.pack('<8H', *m['tile_words']) for m in t['metatiles']))
            self.assertEqual(attrs,b''.join(struct.pack('<H',m['attribute_word']) for m in t['metatiles']))

    def test_all_warp_destinations_zero_based(self):
        self.assertEqual(len(self.data['warp_links']), 13)
        for link in self.data['warp_links']:
            src = self.maps[link['source_map']]['warp_events'][link['source_warp']]
            dst = self.maps[link['dest_map']]['warp_events'][int(src['dest_warp_id'])]
            self.assertEqual(link['dest_xy'], [dst['x'],dst['y']])
        town = self.maps['MAP_LITTLEROOT_TOWN']
        self.assertEqual(town['warp_events'][1]['dest_warp_id'], '1')
        # A one-based conversion would silently land on the house's other exit.
        house = self.maps['MAP_LITTLEROOT_TOWN_BRENDANS_HOUSE_1F']
        self.assertEqual(house['warp_events'][2]['dest_map'], 'MAP_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F')

    def test_variant_padding_preserved_not_geometry(self):
        v, = self.data['layout_variants']
        self.assertEqual(len(v['cells']), 13*13)
        raw = (SOURCE/v['blockdata_filepath']).read_bytes()
        all_words = [c['source_word'] for c in v['cells']] + v['trailing_block_words']
        self.assertEqual(raw, struct.pack('<'+'H'*len(all_words),*all_words))
        self.assertEqual(len(v['trailing_block_words']), 1)

    def test_script_source_locations_and_roots(self):
        self.assertEqual(self.data['missing_entrypoints'], [])
        for label, item in self.data['scripts'].items():
            lines = (SOURCE/item['source']).read_text().splitlines()
            self.assertTrue(lines[item['line']-1].startswith(label+':'))
        for m in self.data['maps']:
            self.assertIn(m['name']+'_MapScripts', self.data['scripts'])

    def test_source_behavior_enum_resolved(self):
        # Engine semantic dispatch needs source enums, not just unnamed numbers.
        town = self.maps['MAP_LITTLEROOT_TOWN']
        for warp in town['warp_events']:
            g=town['geometry']
            cell=g['cells'][warp['y']*g['width']+warp['x']]
            self.assertEqual(cell['behavior'], 0x69)
            self.assertEqual(cell['behavior_name'], 'MB_ANIMATED_DOOR')
        for m in self.data['maps']:
            for c in m['geometry']['cells']:
                self.assertIsNotNone(c['behavior_name'])

    def test_input_hashes_match_actual_bytes(self):
        for path, digest in self.data['source_hashes'].items():
            self.assertEqual(digest, hashlib.sha256((SOURCE/path).read_bytes()).hexdigest())

if __name__ == '__main__':
    unittest.main()
