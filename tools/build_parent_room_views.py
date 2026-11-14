"""Supplemental contact cameras on exact copies of the source-built rooms."""
import hashlib,json,math
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1];EAL=unreal.EditorAssetLibrary;LEVEL=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);ACTORS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rows=[];source_maps={m['name']:m['id'] for m in json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/littleroot.json').read_text())['maps']}
for short,room,role,tile,loc in [('Brendan','LittlerootTown_BrendansHouse_1F','mom',[2,6],[650,1650,260]),('May','LittlerootTown_MaysHouse_1F','rival_mom',[8,7],[1350,1650,260])]:
    source='/Game/Maps/'+room;target='/Game/QualityGallery/Parent'+short+'Room';file=ROOT/'unreal/Emerald/Content/Maps'/(room+'.umap');before=hashlib.sha256(file.read_bytes()).hexdigest()
    if EAL.does_asset_exist(target) and not EAL.delete_asset(target):raise RuntimeError('Cannot replace owned supplemental contact map')
    if not EAL.duplicate_asset(source,target) or not LEVEL.load_level(target):raise RuntimeError('Cannot copy source room for contact camera')
    for a in ACTORS.get_all_level_actors():
        if a.get_class().get_name()=='CameraActor':raise RuntimeError('Source room already contains an unexpected camera')
    focus=[tile[0]*200,tile[1]*200,115];delta=[b-a for a,b in zip(loc,focus)];yaw=math.degrees(math.atan2(delta[1],delta[0]));pitch=math.degrees(math.atan2(delta[2],math.hypot(delta[0],delta[1])))
    camera=ACTORS.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*loc),unreal.Rotator(pitch=pitch,yaw=yaw,roll=0));camera.set_actor_label('EmeraldGenerated_ParentContactCamera');camera.set_editor_property('tags',[unreal.Name('EmeraldGenerated')]);camera.set_editor_property('auto_activate_for_player',unreal.AutoReceiveInput.PLAYER0);camera.camera_component.set_editor_property('field_of_view',60.)
    if not LEVEL.save_current_level():raise RuntimeError('Contact camera not saved')
    if hashlib.sha256(file.read_bytes()).hexdigest()!=before:raise RuntimeError('Original source-built room changed while copying contact view')
    rows.append({'map':target,'source_level':source,'source_level_sha256':before,'original_level_unchanged':True,'role':role,'source_map':source_maps[room],'source_tile':tile,'camera_cm':loc,'camera_focus_cm':focus,'fov':60,'scope':'Supplemental camera only on copied source-built scene; runtime source objects/anchors/layout and original scene bytes retained. Not a locked hero replacement.'})
(ROOT/'data/native-parent-room-views-report.json').write_text(json.dumps({'views':rows,'inspection_complete':False,'quality_gate_passed':False},indent=2)+'\n')
print('Saved two source-room contact cameras; original level bytes unchanged')
