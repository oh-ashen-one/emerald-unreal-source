#!/usr/bin/env python3
"""Install the attributed adult for an existing source scientist graphics role."""
import json,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def install():
    proof=json.loads((ROOT/'data/native-adult-gallery-report.json').read_text());credits=json.loads((ROOT/'data/native-asset-credits-report.json').read_text())
    if not proof.get('inspection_complete') or not proof.get('runtime_playback_verified') or not credits.get('inspection_complete') or not credits.get('native_input_verified'):raise SystemExit('Inspect native adult motion and attribution UI before world integration')
    source=json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/quality-adult-profile.json').read_text());path=ROOT/'unreal/Emerald/Content/Imported/Data/character-assets.json';registry=json.loads(path.read_text());old=registry['profiles']['scientist'];profile=copy.deepcopy(source)
    for name in ('height_cm','width_scale','source_graphics','source_visible_height_px'):
        if name in old:profile[name]=old[name]
    profile.update(model='CaninoGameMan',appearance='Licensed original adult appearance and PBR adapters; source role/height/coordinates/facing/flags retained',attribution='Canino3d Studio - CC BY 4.0; C Credits provides source/license/modification notice')
    registry['profiles']['scientist']=profile;temp=path.with_suffix('.tmp');temp.write_text(json.dumps(registry,indent=2)+'\n');temp.replace(path)
    (ROOT/'data/native-adult-integration-report.json').write_text(json.dumps({'role':'scientist','profile':profile,'graphics_map_changed':False,'source_events_changed':False,'source':proof['source'],'license':'CC-BY-4.0','scope':'Existing source scientist role descriptor installed after native preview/attribution checks. Actual world/movement/contact and final quality still require verification.','quality_gate_passed':False},indent=2)+'\n');print('Installed attributed adult for existing scientist role only; source graphics/state/layout unchanged')
if __name__=='__main__':install()
