"""Native FBX evaluation preserving original rig, mesh assembly and morphs."""
import json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1]
if Path(unreal.Paths.get_project_file_path()).resolve()!=ROOT/'unreal/Emerald/Emerald.uproject':raise RuntimeError('Unexpected project')
EAL=unreal.EditorAssetLibrary;TOOLS=unreal.AssetToolsHelpers.get_asset_tools();LIB=unreal.MaterialEditingLibrary;dest='/Game/Imported/QualityAdults/CaninoGameMan'
options=unreal.FbxImportUI()
for key,value in [('import_as_skeletal',True),('import_mesh',True),('import_animations',False),('import_materials',True),('import_textures',True),('create_physics_asset',False),('mesh_type_to_import',unreal.FBXImportType.FBXIT_SKELETAL_MESH)]:options.set_editor_property(key,value)
options.skeletal_mesh_import_data.set_editor_property('import_morph_targets',True)
options.skeletal_mesh_import_data.set_editor_property('normal_import_method',unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
task=unreal.AssetImportTask()
for key,value in [('filename',str(ROOT/'unreal/Emerald/Content/Imported/QualityAdultSources/Jake.fbx')),('destination_path',dest),('destination_name','CaninoGameMan'),('automated',True),('replace_existing',True),('save',True),('options',options)]:task.set_editor_property(key,value)
TOOLS.import_asset_tasks([task]);meshes=[unreal.load_asset(p) for p in EAL.list_assets(dest,recursive=True) if isinstance(unreal.load_asset(p),unreal.SkeletalMesh)];rows=[];materials={}
if not meshes:raise RuntimeError('Original adult package did not import a skeleton')
for mesh in meshes:
    component=unreal.SkeletalMeshComponent();component.set_skeletal_mesh_asset(mesh);b=mesh.get_bounds();names=[str(component.get_bone_name(i)) for i in range(component.get_num_bones())];mats=[]
    for slot in mesh.get_editor_property('materials'):
        material=slot.get_editor_property('material_interface')
        if material is None:raise RuntimeError('Adult material missing')
        mats.append(material.get_path_name());materials[material.get_path_name()]=material
    morphs=mesh.get_editor_property('morph_targets')
    rows.append({'mesh':mesh.get_path_name(),'skeleton':mesh.get_editor_property('skeleton').get_path_name(),'bones':names,'morph_targets':[m.get_name() for m in morphs],'materials':mats,'bounds_origin':[b.origin.x,b.origin.y,b.origin.z],'bounds_extent':[b.box_extent.x,b.box_extent.y,b.box_extent.z]})
bindings={}
for path,mat in materials.items():
    parent=mat
    while isinstance(parent,unreal.MaterialInstanceConstant):parent=parent.get_editor_property('parent')
    LIB.recompile_material(parent);error=unreal.EmeraldAuthoringLibrary.compile_material(parent)
    if error:raise RuntimeError('Adult shader compilation failed: '+error)
    graph={}
    for label,prop in [('color',unreal.MaterialProperty.MP_BASE_COLOR),('normal',unreal.MaterialProperty.MP_NORMAL),('roughness',unreal.MaterialProperty.MP_ROUGHNESS),('opacity',unreal.MaterialProperty.MP_OPACITY),('opacity_mask',unreal.MaterialProperty.MP_OPACITY_MASK)]:
        pending=[LIB.get_material_property_input_node(parent,prop)];seen=set();textures=set()
        while pending:
            node=pending.pop()
            if node is None or node.get_path_name() in seen:continue
            seen.add(node.get_path_name())
            if isinstance(node,unreal.MaterialExpressionTextureSample):
                texture=node.get_editor_property('texture')
                if texture:textures.add(texture.get_path_name())
            pending.extend(LIB.get_inputs_for_material_expression(parent,node))
        graph[label]=sorted(textures)
    bindings[path]=graph
EAL.save_directory(dest,only_if_is_dirty=False,recursive=True)
(ROOT/'data/native-adult-character-import-report.json').write_text(json.dumps({'source':'https://www.fab.com/listings/d2d871a0-50ea-4041-9889-3f27e5377bb3','creator':'Canino3d Studio','license':'CC-BY-4.0','meshes':rows,'material_graph_textures':bindings,'scope':'Original FBX native evaluation only; complete visual assembly, PBR gaps, motion and role suitability still require inspection. No cast replacement.','quality_gate_passed':False},indent=2)+'\n');print('Native adult FBX import:',len(rows),'mesh assets,',len(materials),'materials')
