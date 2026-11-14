import json
from pathlib import Path
import unittest
from tools.compile_events import split_args,strip_comment,text_value,const_eval,compile_program

ROOT=Path(__file__).resolve().parents[1]

class SourceEventCompiler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.program=compile_program()

    def test_arguments_and_comment_markers_are_not_confused_with_text(self):
        self.assertEqual(split_args('VAR_RESULT, ITEM_TO_BERRY(ITEM_ORAN_BERRY), "a,b"'),['VAR_RESULT','ITEM_TO_BERRY(ITEM_ORAN_BERRY)','"a,b"'])
        self.assertEqual(strip_comment('.string "email@example" @ source comment'),'.string "email@example" ')
        self.assertEqual(text_value('.string "One\\nTwo\\p"\n.string "Three.$"'),'One\nTwo\fThree.')

    def test_c_constant_suffixes_do_not_mangle_identifier_names(self):
        self.assertEqual(const_eval('ITEM_MASTER_BALL + 0x10UL',{'ITEM_MASTER_BALL':7}),23)
        self.assertEqual(const_eval('TRUE | BIT(4)',{}),17)
        self.assertEqual(self.program['constants']['VAR_RESULT'],0x800D)
        self.assertEqual(self.program['constants']['FLAG_SET_WALL_CLOCK'],81)

    def test_all_message_references_and_event_roots_resolve(self):
        self.assertEqual(self.program['missing_roots'],[])
        self.assertEqual(self.program['unresolved_message_labels'],[])
        self.assertIn('gText_PlayerHouseBootPC',self.program['texts'])
        self.assertIn('gText_PokemonTrainerSchoolEmail',self.program['texts'])

    def test_central_noop_helper_and_all_branch_targets_resolve(self):
        self.assertEqual(self.program['unresolved_branch_labels'],[])
        helper=self.program['labels']['Common_EventScript_NopReturn']
        self.assertEqual(helper['source'],'data/event_scripts.s')
        self.assertEqual(helper['commands'][0]['op'],'return')

    def test_movement_contract_is_pinned_source_data(self):
        import hashlib
        p=self.program;c=p['movement_contract']
        self.assertEqual(c['delay_frames'],[32,64,96,128])
        self.assertEqual(c['walk_frames'],16)
        self.assertEqual(c['initial_facing']['MOVEMENT_TYPE_WANDER_LEFT_AND_RIGHT'],3)
        self.assertEqual(c['directions'],[1,2,3,4])
        self.assertEqual(c['blocked_behaviors']['east'],[p['constants'][x] for x in ('MB_IMPASSABLE_EAST','MB_IMPASSABLE_NORTHEAST','MB_IMPASSABLE_SOUTHEAST','MB_IMPASSABLE_WEST_AND_EAST','MB_SECRET_BASE_BREAKABLE_DOOR')])
        for name in ('src/event_object_movement.c','src/data/object_events/movement_type_func_tables.h','src/metatile_behavior.c','include/random.h'):
            self.assertEqual(p['source_hashes'][name],hashlib.sha256((ROOT/'pokeemerald'/name).read_bytes()).hexdigest())

    def test_initial_flags_and_callbacks_are_read_from_original_source(self):
        p=self.program
        self.assertIn('FLAG_HIDE_LITTLEROOT_TOWN_MOM_OUTSIDE',p['initial_flags'])
        self.assertIn('FLAG_HIDE_LITTLEROOT_TOWN_BIRCHS_LAB_BIRCH',p['initial_flags'])
        self.assertEqual(p['callbacks']['MAP_LITTLEROOT_TOWN']['MAP_SCRIPT_ON_TRANSITION'],'LittlerootTown_OnTransition')
        self.assertEqual(p['local_ids']['MAP_LITTLEROOT_TOWN']['LOCALID_LITTLEROOT_TWIN'],1)
        self.assertEqual(p['local_ids']['MAP_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F']['LOCALID_PLAYERS_HOUSE_2F_MOM'],14)

if __name__=='__main__':unittest.main()
