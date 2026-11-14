#!/usr/bin/env python3
"""Install reviewed detailed role descriptors, preserving source identities."""
import copy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def install():
    proof=json.loads((ROOT/'data/native-cast-gallery-report.json').read_text())
    if not proof.get('inspection_complete') or not proof.get('native_idle_playback_verified'):raise SystemExit('Inspect complete native cast preview before integration')
    for name,key in [('native-boy-character-gallery-report.json','runtime_modular_playback_verified'),('native-adult-gallery-report.json','runtime_playback_verified')]:
        base=json.loads((ROOT/'data'/name).read_text())
        if not base.get('inspection_complete') or not base.get(key):raise SystemExit('Base sourced motion review missing')
    path=ROOT/'unreal/Emerald/Content/Imported/Data/character-assets.json'
    registry=json.loads(path.read_text());before=copy.deepcopy(registry)
    for row in proof['roles']:
        role=row['role'];old=registry['profiles'][role];profile=copy.deepcopy(row['profile'])
        for key in ('height_cm','width_scale','source_graphics','source_visible_height_px'):
            if key in old and profile.get(key)!=old[key]:raise SystemExit('Source role contract differs: '+role+'/'+key)
        registry['profiles'][role]=profile
    if any(registry[key]!=before[key] for key in registry if key!='profiles'):raise SystemExit('Source graphics/player mapping changed')
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(registry,indent=2)+'\n');temporary.replace(path)
    (ROOT/'data/native-cast-integration-report.json').write_text(json.dumps({'roles':[r['role'] for r in proof['roles']],'preview':proof['inspected_run'],'graphics_map_changed':False,'source_events_changed':False,'scope':'Five reviewed detailed descriptors installed. Source-world captures/traversal/contact checks required; shared adult appearance remains interim. Riya and remaining female roles unchanged.','quality_gate_passed':False},indent=2)+'\n')
    print('Installed five reviewed detailed descriptors; source mappings unchanged')
if __name__=='__main__':install()
