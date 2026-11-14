import copy
import json
from pathlib import Path
import unittest
from tools.visual_plan import compile_plans

ROOT=Path(__file__).resolve().parents[1]

class SourceFurnishingCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/littleroot.json').read_text())
        compiled=compile_plans(cls.data)
        cls.plans={**compiled['houses'],**compiled['labs']}

    def test_all_blocked_source_cells_have_explicit_disposition(self):
        for m in self.data['maps']:
            if m['name'] not in self.plans: continue
            p=self.plans[m['name']]
            blocked={(c['x'],c['y']) for c in m['geometry']['cells'] if c['collision']}
            coverage={tuple(c['xy']) for c in p['blocked_coverage']}
            diagnostics={tuple(c['xy']) for c in p['diagnostics']}
            self.assertFalse(coverage & diagnostics)
            self.assertEqual(coverage | diagnostics,blocked)

    def test_both_house_roles_have_source_footprint_centers(self):
        expected={
            'LittlerootTown_BrendansHouse_1F':('SourceDiningTable',[700,1300,0]),
            'LittlerootTown_MaysHouse_1F':('SourceDiningTable',[1300,1300,0]),
            'LittlerootTown_BrendansHouse_2F':('SourceBed',[200,900,0]),
            'LittlerootTown_MaysHouse_2F':('SourceBed',[1400,900,0])}
        for name,(kind,center) in expected.items():
            objects=[o for o in self.plans[name]['objects'] if o['id'].startswith(kind+'_')]
            self.assertEqual(len(objects),1)
            self.assertEqual(objects[0]['center_cm'],center)
            if name.endswith('_1F'):
                self.assertEqual(sum(o['id'].startswith('SourceDiningChair_') for o in self.plans[name]['objects']),4)

    def test_source_rugs_are_centered_and_use_each_house_palette(self):
        for name,xy in [('LittlerootTown_BrendansHouse_2F',[1100,900]),('LittlerootTown_MaysHouse_2F',[500,900])]:
            rug,=[o for o in self.plans[name]['objects'] if o['id'].startswith('SourceRug_')]
            self.assertEqual(rug['center_cm'][:2],xy)
            self.assertEqual(rug['size_cm'][:2],[780,780])
            self.assertEqual(rug['material'],'RugPink' if 'Mays' in name else 'Rug')

    def test_lab_compounds_preserve_bg_anchors_and_machine_footprint(self):
        name='LittlerootTown_ProfessorBirchsLab'
        p=self.plans[name]
        self.assertEqual(p['diagnostics'],[])
        objects=p['objects'];by_id={o['id']:o for o in objects}
        self.assertEqual(len(by_id),len(objects))
        desks=[o for o in objects if o['asset']=='desk']
        self.assertEqual(len(desks),4)
        self.assertEqual(by_id['SourceSidePCDesk_1_10']['center_cm'],[200,2000,0])
        self.assertEqual(by_id['SourceSidePCDesk_11_10']['center_cm'],[2200,2000,0])
        self.assertEqual({tuple(p) for p in by_id['SourceLabAnalyzer_10_7']['source_cells']},
                         {(10,6),(11,6),(10,7),(11,7)})
        self.assertEqual(by_id['SourceAnalyzerController_12_7']['source_cells'],[[12,7]])
        m=next(m for m in self.data['maps'] if m['name']==name)
        for e in m['bg_events']:
            xy=[e['x'],e['y']]
            self.assertTrue(any(xy in o['source_cells'] for o in objects),e)

    def test_changed_lab_compound_fails_closed(self):
        data=copy.deepcopy(self.data)
        m=next(m for m in data['maps'] if 'Professor' in m['name'])
        c=next(c for c in m['geometry']['cells'] if (c['x'],c['y'])==(4,1))
        c['metatile_id']=0x202
        with self.assertRaisesRegex(ValueError,'changed source compound'):
            compile_plans(data)

    def test_bedroom_wall_fixtures_keep_mirrored_source_columns(self):
        for name,clockx,mapx,consolex in [('LittlerootTown_BrendansHouse_2F',5,2,3),('LittlerootTown_MaysHouse_2F',3,6,5)]:
            p=self.plans[name]
            for asset,x in [('wallClock',clockx),('regionMapFrame',mapx)]:
                item,=[o for o in p['objects'] if o['asset']==asset]
                self.assertEqual(item['source_anchor'],[x,1])
                self.assertEqual(item['center_cm'][0],x*200)
                self.assertEqual(item['source_cells'],[[x,0],[x,1]])
            console,=[o for o in p['objects'] if o['id'].startswith('SourceGameConsole_')]
            self.assertEqual(console['source_anchor'],[consolex,1])
            self.assertEqual(console['source_cells'],[[consolex,0],[consolex,1]])
            self.assertEqual(p['diagnostics'],[])

    def test_changed_source_compound_fails_closed(self):
        data=copy.deepcopy(self.data)
        m=next(m for m in data['maps'] if m['name']=='LittlerootTown_BrendansHouse_1F')
        c=next(c for c in m['geometry']['cells'] if c['metatile_id']==0x21B)
        c['metatile_id']=0x201
        with self.assertRaisesRegex(ValueError,'changed source compound'):
            compile_plans(data)

if __name__=='__main__': unittest.main()
