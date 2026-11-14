"""Native skeletal import, with exact assembly/clip/skeleton readback."""
import hashlib,json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1]
if Path(unreal.Paths.get_project_file_path()).resolve()!=ROOT/'unreal/Emerald/Emerald.uproject':raise RuntimeError('Unexpected project')
EAL=unreal.EditorAssetLibrary;TOOLS=unreal.AssetToolsHelpers.get_asset_tools()
prep=json.loads((ROOT/'data/character-preparation-report.json').read_text());report={}
oldpath=ROOT/'unreal/Emerald/Content/Imported/Data/character-import-report.json'
previous=json.loads(oldpath.read_text()) if oldpath.exists() else {}
for name,item in prep.items():
    source=ROOT/item['path']
    if hashlib.sha256(source.read_bytes()).hexdigest()!=item['staged_sha256']:raise RuntimeError('Staged character changed')
    dest='/Game/Imported/Characters/'+name
    if not EAL.does_directory_exist(dest) or previous.get(name,{}).get('staged_sha256')!=item['staged_sha256']:
        task=unreal.AssetImportTask()
        for k,v in [('filename',str(source)),('destination_path',dest),('automated',True),('replace_existing',True),('save',True)]:task.set_editor_property(k,v)
        TOOLS.import_asset_tasks([task])
    paths=EAL.list_assets(dest,recursive=True);meshes=[unreal.load_asset(p) for p in paths if isinstance(unreal.load_asset(p),unreal.SkeletalMesh)]
    if len(meshes)!=1:raise RuntimeError('Require exactly one complete skeletal mesh for '+name+': '+str([m.get_path_name() for m in meshes]))
    mesh=meshes[0];skeleton=mesh.get_editor_property('skeleton');anims={}
    for clip in item['selected_clips']:
        found=[unreal.load_asset(p) for p in paths if isinstance(unreal.load_asset(p),unreal.AnimSequence) and (unreal.load_asset(p).get_name() in (clip,name+clip) or unreal.load_asset(p).get_name().endswith('_'+clip))]
        if len(found)!=1:raise RuntimeError('Require one original clip '+name+' '+clip+': '+str([a.get_name() for a in found]))
        a=found[0]
        if a.get_editor_property('skeleton')!=skeleton:raise RuntimeError('Imported clip skeleton mismatch')
        if a.get_play_length()<=0:raise RuntimeError('Empty original animation')
        anims[clip]={'asset':a.get_path_name(),'length_s':a.get_play_length()}
    b=mesh.get_bounds()
    slots=[str(s.get_editor_property('material_slot_name')) for s in mesh.get_editor_property('materials')]
    report[name]={'mesh':mesh.get_path_name(),'skeleton':skeleton.get_path_name(),'animations':anims,'animation_aliases':item['animation_aliases'],'bounds_origin':[b.origin.x,b.origin.y,b.origin.z],'bounds_extent':[b.box_extent.x,b.box_extent.y,b.box_extent.z],'material_slots':slots,'source_joint_count':len(item['joint_names']),'staged_sha256':item['staged_sha256'],'playback_verified':False}
    unreal.log('EMERALD_CHARACTER_IMPORT '+name+' '+json.dumps(report[name]))
output=ROOT/'unreal/Emerald/Content/Imported/Data/character-import-report.json';output.write_text(json.dumps(report,indent=2)+'\n')
EAL.save_directory('/Game/Imported/Characters',only_if_is_dirty=True,recursive=True)
unreal.log('EMERALD_CHARACTER_IMPORT complete')
