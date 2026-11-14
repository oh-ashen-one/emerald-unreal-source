#!/usr/bin/env python3
"""Install reviewed parent variants without changing source object state."""
import copy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def install():
    proof=json.loads((ROOT/'data/native-parent-gallery-report.json').read_text())
    if not all(proof.get(k) for k in ('inspection_complete','runtime_playback_verified','motion_video_inspected')):raise SystemExit('Inspect parent states and actual native motion before integration')
    path=ROOT/'unreal/Emerald/Content/Imported/Data/character-assets.json';registry=json.loads(path.read_text());before=copy.deepcopy(registry)
    if set(proof['profiles'])!={'mom','rival_mom'}:raise SystemExit('Unexpected parent roles')
    for role,profile in proof['profiles'].items():
        old=registry['profiles'][role]
        for key in ('height_cm','width_scale','source_graphics','source_visible_height_px'):
            if key in old and old[key]!=profile.get(key):raise SystemExit('Source role contract differs '+role+'/'+key)
        if len(profile['materials'])!=31 or profile['source_joint_count']!=112 or len(profile.get('seated_offset_cm',[]))!=3:raise SystemExit('Complete measured parent descriptor required')
        registry['profiles'][role]=copy.deepcopy(profile)
    if any(registry[k]!=before[k] for k in registry if k!='profiles'):raise SystemExit('Source graphics/player mapping changed')
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(registry,indent=2)+'\n');temporary.replace(path)
    (ROOT/'data/native-parent-integration-report.json').write_text(json.dumps({'roles':['mom','rival_mom'],'preview':proof['inspected_run'],'motion_preview':proof['motion_run'],'graphics_map_changed':False,'source_events_changed':False,'source_anchors_changed':False,'scope':'Two reviewed complete parent descriptors installed with measured visual-only seating offset. Source-world contact/scale/motion and regressions remain to be checked.','quality_gate_passed':False},indent=2)+'\n')
    print('Installed two reviewed detailed parent descriptors; source identities/anchors unchanged')
if __name__=='__main__':install()
