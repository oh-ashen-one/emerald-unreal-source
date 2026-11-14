#!/usr/bin/env python3
"""Install the verified modular child candidate without changing source events."""
import copy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def install():
    proof=json.loads((ROOT/'data/native-quality-character-gallery-report.json').read_text())
    if not proof.get('runtime_modular_playback_verified') or not proof.get('inspection_complete'):raise SystemExit('Inspect complete native modular playback before integration')
    candidate=json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/quality-girl-profile.json').read_text())
    if len(candidate.get('mesh_parts',[]))!=8:raise SystemExit('Complete nine-part candidate required')
    path=ROOT/'unreal/Emerald/Content/Imported/Data/character-assets.json';data=json.loads(path.read_text());prior=copy.deepcopy(data['profiles']['twin']);profile=copy.deepcopy(candidate)
    for key in ('height_cm','width_scale','source_graphics','source_visible_height_px'):
        if key in prior:profile[key]=prior[key]
    profile.update(model='Fab_CartoonCuteGirl',appearance='Licensed original PBR child appearance; source role, visible-height contract, coordinates/facing/flags remain authoritative')
    data['profiles']['twin']=profile;temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(data,indent=2)+'\n');temporary.replace(path)
    (ROOT/'data/native-quality-character-integration-report.json').write_text(json.dumps({'role':'twin','profile':profile,'source_graphics_map_changed':False,'source_events_changed':False,'native_preview':proof.get('inspected_run'),'scope':'Role descriptor installed after complete native modular preview. Actual source-world render/movement, contacts and final quality still require verification.','quality_gate_passed':False},indent=2)+'\n');print('Installed complete licensed child model for existing twin graphics only; source events/layout unchanged')
if __name__=='__main__':install()
