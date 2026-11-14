"""Adapt eye-export materials with native skeletal slot/readback checks."""
import json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1];eal=unreal.EditorAssetLibrary
if Path(unreal.Paths.get_project_file_path()).resolve()!=ROOT/'unreal/Emerald/Emerald.uproject':raise RuntimeError('Unexpected project')
report=json.loads((ROOT/'data/native-boy-character-import-report.json').read_text());clear=unreal.load_asset('/Game/Imported/Materials/FixtureClearGlass')
if clear is None:raise RuntimeError('Existing transparent project material missing')
unreal.MaterialEditingLibrary.set_material_usage(clear,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH)
if not clear.get_editor_property('used_with_skeletal_mesh'):raise RuntimeError('Clear eye material skeletal usage missing')
unreal.MaterialEditingLibrary.recompile_material(clear);error=unreal.EmeraldAuthoringLibrary.compile_material(clear)
if error:raise RuntimeError('Eye-overlay adapter compile failed: '+error)
eal.save_loaded_asset(clear,only_if_is_dirty=False)
rows=[];tools=unreal.AssetToolsHelpers.get_asset_tools();lib=unreal.MaterialEditingLibrary;folder='/Game/Imported/QualityBoyMaterials';eal.make_directory(folder)
for row in report['meshes']:
    mesh=unreal.load_asset(row['asset']);slots=mesh.get_editor_property('materials');expected=[slot.get_editor_property('material_interface').get_path_name() for slot in slots]
    for i,path in enumerate(row['materials']):
        name=path.rsplit('/',1)[-1].split('.')[0]
        if name.startswith(('Std_Eye_Occlusion_','Std_Cornea_')):
            slot=slots[i];slot.set_editor_property('material_interface',clear);slots[i]=slot;expected[i]=clear.get_path_name();rows.append({'mesh':mesh.get_path_name(),'slot':i,'original':path,'assigned':clear.get_path_name(),'reason':'Original exported eye layers rendered incorrectly. Use transparent project adapter while preserving iris textures and complete geometry/rig; final layer optics remain unaccepted.'})
        elif name in ('Std_Eye_R','Std_Eye_L'):
            original=unreal.load_asset(path);target=folder+'/'+name
            material=unreal.load_asset(target) if eal.does_asset_exist(target) else tools.create_asset(name,folder,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
            lib.set_material_instance_parent(material,original);normal=unreal.load_asset('/Engine/EngineMaterials/DefaultNormal')
            if not isinstance(normal,unreal.Texture2D):raise RuntimeError('Native default tangent normal absent')
            lib.set_material_instance_texture_parameter_value(material,'NormalTexture',normal);lib.update_material_instance(material)
            if lib.get_material_instance_texture_parameter_value(material,'NormalTexture')!=normal:raise RuntimeError('Eye normal override readback differs')
            eal.save_loaded_asset(material,only_if_is_dirty=False);slot=slots[i];slot.set_editor_property('material_interface',material);slots[i]=slot;expected[i]=material.get_path_name()
            rows.append({'mesh':mesh.get_path_name(),'slot':i,'original':path,'assigned':material.get_path_name(),'reason':'Original GLB iris normal is a single-channel constant122 image, not a tangent RGB normal. Reuse native flat normal while retaining creator eye color/roughness maps.'})
    mesh.set_editor_property('materials',slots);actual=[slot.get_editor_property('material_interface').get_path_name() for slot in mesh.get_editor_property('materials')]
    if actual!=expected:raise RuntimeError('Native skeletal material-slot assignment did not persist '+mesh.get_name())
    eal.save_loaded_asset(mesh,only_if_is_dirty=False)

if len(rows)!=6:raise RuntimeError('Expected four cornea/occlusion and two iris-normal adapters')
(ROOT/'data/native-boy-material-adaptation-report.json').write_text(json.dumps({'source_license':'Fab Standard License','changes':rows,'native_slot_readback_verified':True,'geometry_skin_or_source_bytes_changed':False,'scope':'Eye-overlay material adapter only. Inspect rendered eyes before acceptance; original iris color/roughness and skin/cloth/hair maps retained in rendering; cornea/occlusion use the transparent adapter.','quality_gate_passed':False},indent=2)+'\n')
print('Verified six native eye material assignments; actual portrait review required')

# Rebuild the owned preview in this initialized editor after material updates.
import runpy
runpy.run_path(str(ROOT/'tools/build_boy_gallery.py'),run_name='__main__')
