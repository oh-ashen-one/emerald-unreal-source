"""Licensed PBR surface adapters; preserve original geometry, rig and color maps."""
import json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1];EAL=unreal.EditorAssetLibrary;TOOLS=unreal.AssetToolsHelpers.get_asset_tools();LIB=unreal.MaterialEditingLibrary
original=json.loads((ROOT/'data/native-adult-character-import-report.json').read_text());child=json.loads((ROOT/'data/native-quality-character-import-report.json').read_text());folder='/Game/Imported/QualityAdultMaterials';EAL.make_directory(folder);rows={}
child_materials={p.rsplit('/',1)[-1].split('.')[0]:p for p in child['material_bindings']}
def compile_material(mat):
    LIB.recompile_material(mat);error=unreal.EmeraldAuthoringLibrary.compile_material(mat)
    if error:raise RuntimeError('Adult adapted material compile failed: '+error)
for row in original['meshes']:
    mesh=unreal.load_asset(row['mesh']);slots=mesh.get_editor_property('materials');expected=[]
    if len(slots)!=len(row['materials']):raise RuntimeError('Original adult material-slot count changed')
    for i,path in enumerate(row['materials']):
        name=path.rsplit('/',1)[-1].split('.')[0];source=unreal.load_asset(path);target=folder+'/PBR_'+name;kind='Original material retained';mat=source
        if name in ('Std_Skin_Head','Std_Skin_Body','Std_Skin_Arm','Std_Skin_Leg','Std_Nails'):
            target=folder+'/SourcePBR_'+name
            if not isinstance(source,unreal.Material):raise RuntimeError('Expected original FBX skin graph')
            mat=unreal.load_asset(target) if EAL.does_asset_exist(target) else EAL.duplicate_asset(path,target)
            expressions=list(LIB.get_material_expressions(mat));parent_path=child_materials[name];rough_path=child['material_bindings'][parent_path]['MetallicRoughnessTexture'];texture_path=folder+'/T_Roughness_'+name
            texture=unreal.load_asset(texture_path) if EAL.does_asset_exist(texture_path) else EAL.duplicate_asset(rough_path,texture_path)
            texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS);texture.set_editor_property('srgb',False);texture.set_editor_property('virtual_texture_streaming',False);EAL.save_loaded_asset(texture,only_if_is_dirty=False)
            if not isinstance(texture,unreal.Texture2D):raise RuntimeError('Licensed skin roughness map absent')
            found=[n for n in expressions if isinstance(n,unreal.MaterialExpressionTextureSampleParameter2D) and str(n.get_editor_property('parameter_name'))=='SkinRoughness']
            node=found[0] if found else LIB.create_material_expression(mat,unreal.MaterialExpressionTextureSampleParameter2D,0,0)
            node.set_editor_property('parameter_name','SkinRoughness');node.set_editor_property('texture',texture);node.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
            if not LIB.connect_material_property(node,'G',unreal.MaterialProperty.MP_ROUGHNESS):raise RuntimeError('Skin roughness graph connection failed')
            constants=[n for n in expressions if isinstance(n,unreal.MaterialExpressionScalarParameter) and str(n.get_editor_property('parameter_name'))=='SkinMetallic']
            zero=constants[0] if constants else LIB.create_material_expression(mat,unreal.MaterialExpressionScalarParameter,0,0);zero.set_editor_property('parameter_name','SkinMetallic');zero.set_editor_property('default_value',0.)
            if not LIB.connect_material_property(zero,'',unreal.MaterialProperty.MP_METALLIC):raise RuntimeError('Nonmetal skin connection failed')
            LIB.set_material_usage(mat,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH);compile_material(mat);kind='Original FBX color/normal shader graph preserved; existing licensed CC-style skin roughness G map added explicitly, metallic0. Original UV/color factors retained.'
        elif name in ('lambert3SG','lambert4','lambert5'):
            mat=unreal.load_asset(target) if EAL.does_asset_exist(target) else EAL.duplicate_asset(path,target)
            # Rebuild from a fresh duplicate only once; parameter nodes are
            # reused by name on subsequent runs, keeping original color graph.
            expressions=list(LIB.get_material_expressions(mat))
            def parameter(cls,label):
                found=[n for n in expressions if isinstance(n,cls) and str(n.get_editor_property('parameter_name'))==label]
                return found[0] if found else LIB.create_material_expression(mat,cls,0,0)
            uv=next((n for n in expressions if isinstance(n,unreal.MaterialExpressionTextureCoordinate) and abs(n.get_editor_property('u_tiling')-16.)<.01),None)
            if uv is None:uv=LIB.create_material_expression(mat,unreal.MaterialExpressionTextureCoordinate,0,0)
            uv.set_editor_property('u_tiling',16.);uv.set_editor_property('v_tiling',16.)
            for label,texture_path,kind_sampler,prop,pin in [('FabricNormal','/Game/Imported/Surfaces/QualityFabric_nor_dx',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,unreal.MaterialProperty.MP_NORMAL,'RGB'),('FabricARM','/Game/Imported/Surfaces/QualityFabric_arm',unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,unreal.MaterialProperty.MP_ROUGHNESS,'G')]:
                node=parameter(unreal.MaterialExpressionTextureSampleParameter2D,label);node.set_editor_property('parameter_name',label);node.set_editor_property('texture',unreal.load_asset(texture_path));node.set_editor_property('sampler_type',kind_sampler)
                if not LIB.connect_material_expressions(uv,'',node,'UVs') or not LIB.connect_material_property(node,pin,prop):raise RuntimeError('Cloth detail connection failed')
            compile_material(mat);kind='Original creator color graph plus CC0 Denim Fabric03 real normal/roughness maps at16xUV microdetail'
        elif name.startswith('Std_Cornea_'):
            mat=unreal.load_asset('/Game/Imported/Materials/FixtureClearGlass');LIB.set_material_usage(mat,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH);compile_material(mat);EAL.save_loaded_asset(mat,only_if_is_dirty=False);kind='Existing transparent clear-glass parent replaces opaque FBX cornea layer; iris color geometry retained'
        if mat is None:raise RuntimeError('Adapted adult material missing')
        if isinstance(mat,unreal.MaterialInstanceConstant):
            parent=mat
            while isinstance(parent,unreal.MaterialInstanceConstant):parent=parent.get_editor_property('parent')
            compile_material(parent)
        if mat is not source and mat.get_path_name().startswith(folder):EAL.save_loaded_asset(mat,only_if_is_dirty=False)
        slot=slots[i];slot.set_editor_property('material_interface',mat);slots[i]=slot;expected.append(mat.get_path_name());bindings={}
        for parameter in LIB.get_texture_parameter_names(mat):
            texture=LIB.get_material_instance_texture_parameter_value(mat,parameter) if isinstance(mat,unreal.MaterialInstanceConstant) else LIB.get_material_default_texture_parameter_value(mat,parameter)
            bindings[str(parameter)]=texture.get_path_name() if texture else None
        if name in ('lambert3SG','lambert4','lambert5') and (not bindings.get('FabricNormal') or not bindings.get('FabricARM')):raise RuntimeError('Required cloth PBR bindings absent')
        rows[name]={'original':path,'assigned':mat.get_path_name(),'adaptation':kind,'texture_bindings':bindings}
    mesh.set_editor_property('materials',slots)
    actual=[slot.get_editor_property('material_interface').get_path_name() for slot in mesh.get_editor_property('materials')]
    if actual!=expected:raise RuntimeError('Native adult skeletal material-slot readback differs')
    EAL.save_loaded_asset(mesh,only_if_is_dirty=False)
(ROOT/'data/native-adult-material-adaptation-report.json').write_text(json.dumps({'materials':rows,'base_license':'Canino3d Studio CC BY4.0','additional_sources':['Cartoon Cute Girl Rigged, Fab Standard License: existing skin roughness maps','Denim Fabric03, CC0: normal/roughness microdetail','Original project clear-glass shader'],'native_slot_readback_verified':True,'geometry_or_skin_modified':False,'scope':'Material-only candidate adaptation with actual native mesh-slot readback. Original skin color/normal graph preserved. Fresh rendered comparison/eyes/UV fit and final quality still required.','quality_gate_passed':False},indent=2)+'\n');print('Adapted adult materials without changing original geometry/rig/color files')

import runpy
runpy.run_path(str(ROOT/'tools/build_adult_gallery.py'),run_name='__main__')
