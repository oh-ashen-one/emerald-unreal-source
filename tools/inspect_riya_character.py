"""Read actual supplied native meshes, rig and material dependencies."""
import json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1];lib=unreal.MaterialEditingLibrary;eal=unreal.EditorAssetLibrary
if Path(unreal.Paths.get_project_file_path()).resolve()!=ROOT/'unreal/Emerald/Emerald.uproject':raise RuntimeError('Unexpected owned project')
registry=unreal.AssetRegistryHelpers.get_asset_registry();registry.scan_paths_synchronous(['/Game/Realisticgirl'],force_rescan=True)
rows=[];materials={}
for asset in registry.get_assets_by_path('/Game/Realisticgirl',recursive=True):
    if str(asset.asset_class_path.asset_name)!='SkeletalMesh':continue
    mesh=asset.get_asset();component=unreal.SkeletalMeshComponent();component.set_skeletal_mesh_asset(mesh);bounds=mesh.get_bounds();slots=mesh.get_editor_property('materials')
    for slot in slots:
        mat=slot.material_interface
        if not mat:raise RuntimeError('Native Riya material absent')
        if mat.get_path_name() in materials:continue
        parent=mat
        while isinstance(parent,unreal.MaterialInstanceConstant):parent=parent.get_editor_property('parent')
        bindings={}
        for name in lib.get_texture_parameter_names(mat):
            texture=lib.get_material_instance_texture_parameter_value(mat,name) if isinstance(mat,unreal.MaterialInstanceConstant) else lib.get_material_default_texture_parameter_value(mat,name)
            bindings[str(name)]=texture.get_path_name() if texture else None
        materials[mat.get_path_name()]={'parent':parent.get_path_name(),'blend_mode':str(parent.get_editor_property('blend_mode')),'texture_parameters':bindings}
    native_data=unreal.AssetRegistryHelpers.create_asset_data(mesh)
    rows.append({'mesh':mesh.get_path_name(),'native_triangles':unreal.AssetRegistryHelpers.get_tag_value(native_data,'Triangles'),'native_vertices':unreal.AssetRegistryHelpers.get_tag_value(native_data,'Vertices'),'morph_targets':[v.get_name() for v in mesh.get_editor_property('morph_targets')],'skeleton':mesh.get_editor_property('skeleton').get_path_name(),'bones':[str(component.get_bone_name(i)) for i in range(component.get_num_bones())],'materials':[s.material_interface.get_path_name() for s in slots],'material_slots':[str(s.material_slot_name) for s in slots],'bounds_origin':[bounds.origin.x,bounds.origin.y,bounds.origin.z],'bounds_extent':[bounds.box_extent.x,bounds.box_extent.y,bounds.box_extent.z]})
if not rows:raise RuntimeError('Supplied native Riya skeletal meshes unavailable')
(ROOT/'data/native-riya-import-report.json').write_text(json.dumps({'meshes':rows,'materials':materials,'source':'https://www.fab.com/listings/40fcda7b-ca5b-4d0a-a8d1-eef4d79867e7','license':'Fab Standard License','scope':'Native mesh/rig/material readback only; complete assembly/appearance/motion/role fit requires inspected preview','quality_gate_passed':False},indent=2)+'\n')
print('Native Riya meshes',[(r['mesh'].split('/')[-1],len(r['bones']),len(r['materials'])) for r in rows])
