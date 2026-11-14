#!/usr/bin/env python3
"""Install the complete verified boy for the existing male-player profile only."""
import copy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def install():
    proof=json.loads((ROOT/'data/native-boy-character-gallery-report.json').read_text());materials=json.loads((ROOT/'data/native-boy-material-adaptation-report.json').read_text())
    if not proof.get('runtime_modular_playback_verified') or not proof.get('inspection_complete') or not materials.get('inspection_complete'):raise SystemExit('Inspect complete native boy motion and corrected eyes before integration')
    candidate=json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/quality-boy-profile.json').read_text())
    if len(candidate.get('mesh_parts',[]))!=10:raise SystemExit('Complete eleven-part boy required')
    path=ROOT/'unreal/Emerald/Content/Imported/Data/character-assets.json';data=json.loads(path.read_text());prior=copy.deepcopy(data['profiles']['player_male']);profile=copy.deepcopy(candidate)
    for key in ('height_cm','width_scale','source_graphics','source_visible_height_px'):
        if key in prior:profile[key]=prior[key]
    profile.update(model='Fab_CartoonYoungBoy',appearance='Licensed original PBR boy appearance; source male-player visible-height/graphics/coordinates/facing/flags contract retained')
    graphics=copy.deepcopy(data['graphics']);data['profiles']['player_male']=profile
    if data['graphics']!=graphics:raise SystemExit('Source graphics mapping changed')
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(data,indent=2)+'\n');temporary.replace(path)
    (ROOT/'data/native-boy-integration-report.json').write_text(json.dumps({'role':'player_male','profile':profile,'source_graphics_map_changed':False,'source_events_changed':False,'native_preview':proof.get('inspected_run'),'scope':'Male-player descriptor only installed after complete native motion/eye preview. Actual world traversal/render/contact and final quality still require verification.','quality_gate_passed':False},indent=2)+'\n')
    print('Installed complete licensed boy for existing male-player profile only; source state/layout unchanged')
if __name__=='__main__':install()
