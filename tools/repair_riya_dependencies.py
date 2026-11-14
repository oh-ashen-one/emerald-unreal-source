"""Resolve stale package paths using only assets included in the licensed zip."""
import json,hashlib
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1];eal=unreal.EditorAssetLibrary
if Path(unreal.Paths.get_project_file_path()).resolve()!=ROOT/'unreal/Emerald/Emerald.uproject':raise RuntimeError('Unexpected project')
source='/Game/Realisticgirl/'
aliases=[('material/Functions/MF_MatID','/Game/IdaFaber/Materials/Functions/MF_MatID'),('material/Other/SP_Skin','/Game/IdaFaber/Materials/SP_Skin'),('Textures/T_Placeholder_White','/Game/IdaFaber/Textures/Base/T_Placeholder_White'),('Textures/T_Placeholder_Normal','/Game/IdaFaber/Textures/Base/T_Placeholder_Normal'),('Textures/Hair_T_Transparency_Hair_Root_Map','/Game/IdaFaber/Textures/Base/Wavy/T_HAIR_WAVY_root'),('Textures/T_Placeholder_Black','/Game/IdaFaber/Textures/Base/Wavy/T_HAIR_WAVY_wind')]
file=ROOT/'data/riya-compatibility-alias-report.json';previous=json.loads(file.read_text()) if file.exists() else {};old={v['target']:v for v in previous.get('aliases',[])};rows=[]
for relative,target in aliases:
    origin=source+relative;asset=unreal.load_asset(origin)
    if asset is None:raise RuntimeError('Included replacement dependency absent '+origin)
    if eal.does_asset_exist(target):
        if old.get(target,{}).get('source')!=origin:raise RuntimeError('Unowned compatibility target preserved '+target)
        duplicate=unreal.load_asset(target)
    else:
        eal.make_directory(target.rsplit('/',1)[0]);duplicate=eal.duplicate_asset(origin,target)
    if duplicate is None or duplicate.get_class()!=asset.get_class():raise RuntimeError('Compatibility copy class differs')
    eal.save_loaded_asset(duplicate,only_if_is_dirty=False)
    native=ROOT/'unreal/Emerald/Content'/(target.removeprefix('/Game/')+'.uasset')
    rows.append({'source':origin,'target':target,'class':duplicate.get_class().get_name(),'sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'role':'Zero-wind placeholder from supplied black texture' if target.endswith('_wind') else 'Included licensed dependency copied to stale expected package path'})
file.write_text(json.dumps({'aliases':rows,'external_assets_acquired':False,'license':'Fab Standard License, same supplied Riya archive','source':'https://www.fab.com/listings/40fcda7b-ca5b-4d0a-a8d1-eef4d79867e7','scope':'Project compatibility aliases only, not assets acquired from IdaFaber. Original archive/source copies unchanged. Fresh native render/compile verification required.','quality_gate_passed':False},indent=2)+'\n');print('Created licensed included-asset compatibility aliases',len(rows))
