"""Native complete-skin/PBR import audit; does not replace the runtime cast."""
import json,hashlib
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1]
if Path(unreal.Paths.get_project_file_path()).resolve()!=ROOT/'unreal/Emerald/Emerald.uproject':raise RuntimeError('Unexpected project')
item=json.loads((ROOT/'data/quality-character-preparation-report.json').read_text());source=ROOT/item['file']
if hashlib.sha256(source.read_bytes()).hexdigest()!=item['staged_sha256']:raise RuntimeError('Character derivative differs')
dest='/Game/Imported/QualityCharacters/CartoonCuteGirl';eal=unreal.EditorAssetLibrary;lib=unreal.MaterialEditingLibrary;task=unreal.AssetImportTask()
for key,value in [('filename',str(source)),('destination_path',dest),('automated',True),('replace_existing',True),('save',True)]:task.set_editor_property(key,value)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);paths=eal.list_assets(dest,recursive=True);meshes=[];animations=[];materials={}
for path in paths:
    asset=unreal.load_asset(path)
    if isinstance(asset,unreal.SkeletalMesh):
        component=unreal.SkeletalMeshComponent();component.set_skeletal_mesh_asset(asset);b=asset.get_bounds();mats=[]
        for slot in asset.get_editor_property('materials'):
            material=slot.get_editor_property('material_interface')
            if material is None:raise RuntimeError('Candidate skeletal material missing')
            mats.append(material.get_path_name());materials[material.get_path_name()]=material
        meshes.append({'asset':asset.get_path_name(),'skeleton':asset.get_editor_property('skeleton').get_path_name(),'native_bone_count':component.get_num_bones(),'bounds_origin':[b.origin.x,b.origin.y,b.origin.z],'bounds_extent':[b.box_extent.x,b.box_extent.y,b.box_extent.z],'materials':mats})
    elif isinstance(asset,unreal.AnimSequence):animations.append({'asset':asset.get_path_name(),'skeleton':asset.get_editor_property('skeleton').get_path_name(),'duration':asset.get_play_length(),'scope':'Original facial test only, not locomotion'})
if not meshes:raise RuntimeError('No complete skeletal candidate imported')
roots={};bindings={}
for path,material in materials.items():
    parent=material
    while isinstance(parent,unreal.MaterialInstanceConstant):parent=parent.get_editor_property('parent')
    roots[parent.get_path_name()]=parent;bindings[path]={}
    for name in lib.get_texture_parameter_names(material):
        texture=lib.get_material_instance_texture_parameter_value(material,name) if isinstance(material,unreal.MaterialInstanceConstant) else lib.get_material_default_texture_parameter_value(material,name)
        bindings[path][str(name)]=texture.get_path_name() if texture else None
for parent in roots.values():
    lib.recompile_material(parent);error=unreal.EmeraldAuthoringLibrary.compile_material(parent)
    if error:raise RuntimeError('Character material compile failed: '+error)
eal.save_directory(dest,only_if_is_dirty=False,recursive=True)
report={'meshes':meshes,'animations':animations,'material_bindings':bindings,'source_mesh_parts':item['source_meshes'],'source_triangles':item['source_triangles'],'source_joints':len(item['source_joint_names'][0]),'scope':'Native asset audit only. No runtime cast replacement, no body locomotion/retarget or final visual acceptance yet. All mesh parts must be accounted for before integration.','quality_gate_passed':False}
(ROOT/'data/native-quality-character-import-report.json').write_text(json.dumps(report,indent=2)+'\n');print('Native high-detail candidate meshes:',len(meshes),'materials:',len(materials))
