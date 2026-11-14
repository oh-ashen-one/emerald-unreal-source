"""Source-colored rugs with licensed woven-fabric PBR and a fitted border."""
import json
from material_graph import clear_material

def build(root,unreal,eal,tools,import_surface,palette,compile_material):
    lib=unreal.MaterialEditingLibrary;lock=json.loads((root/'data/quality-textile-lock.json').read_text());textures={}
    for f in lock['files']:
        texture=import_surface(root/f['path'],'QualityFabric_'+f['channel']);texture.set_editor_property('srgb',f['channel']=='Diffuse')
        if f['channel']=='nor_dx':texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
        if f['channel']=='arm':texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
        eal.save_loaded_asset(texture,only_if_is_dirty=False);textures[f['channel']]=texture
    mat_path='/Game/Imported/Materials/QualityWovenRug';mat=unreal.load_asset(mat_path) if eal.does_asset_exist(mat_path) else tools.create_asset('QualityWovenRug','/Game/Imported/Materials',unreal.Material,unreal.MaterialFactoryNew());clear_material(mat,unreal)
    def node(cls):return lib.create_material_expression(mat,cls,0,0)
    def link(a,out,b,pin):
        if not lib.connect_material_expressions(a,out,b,pin):raise RuntimeError('Fabric shader input failed '+pin)
    def output(n,pin,prop):
        if not lib.connect_material_property(n,pin,prop):raise RuntimeError('Fabric shader output failed')
    def custom(code,inputs,kind):
        n=node(unreal.MaterialExpressionCustom);n.set_editor_property('code',code);n.set_editor_property('output_type',kind);rows=[]
        for name in inputs:
            row=unreal.CustomInput();row.set_editor_property('input_name',name);rows.append(row)
        n.set_editor_property('inputs',rows)
        for name,source in inputs.items():link(source,'',n,name)
        return n
    world=node(unreal.MaterialExpressionWorldPosition);uv=custom('return P.xy/100.;',{'P':world},unreal.CustomMaterialOutputType.CMOT_FLOAT2)
    bounds=[]
    for name,value in [('RugCenter',unreal.LinearColor(0,0,0,1)),('RugSize',unreal.LinearColor(1000,1000,1,1))]:
        n=node(unreal.MaterialExpressionVectorParameter);n.set_editor_property('parameter_name',name);n.set_editor_property('default_value',value);bounds.append(n)
    local=custom('return (P.xy-C.xy)/max(S.xy,float2(1,1))+.5;',{'P':world,'C':bounds[0],'S':bounds[1]},unreal.CustomMaterialOutputType.CMOT_FLOAT2)
    samples={}
    for channel,kind in [('Diffuse',unreal.MaterialSamplerType.SAMPLERTYPE_COLOR),('nor_dx',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL),('arm',unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)]:
        n=node(unreal.MaterialExpressionTextureSampleParameter2D);n.set_editor_property('texture',textures[channel]);n.set_editor_property('parameter_name',channel);n.set_editor_property('sampler_type',kind);link(uv,'',n,'UVs');samples[channel]=n
    tint=node(unreal.MaterialExpressionVectorParameter);tint.set_editor_property('parameter_name','SourceTint');tint.set_editor_property('default_value',unreal.LinearColor(.2,.45,.7,1))
    color=custom('float d=min(min(U.x,1-U.x),min(U.y,1-U.y));float border=1-.32*(1-smoothstep(.014,.019,d))-.18*(smoothstep(.028,.031,d)*(1-smoothstep(.038,.041,d)));return T*clamp(dot(C,float3(.2126,.7152,.0722))*3.5,.55,1.25)*border;',{'C':samples['Diffuse'],'T':tint,'U':local},unreal.CustomMaterialOutputType.CMOT_FLOAT3);output(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
    output(samples['nor_dx'],'RGB',unreal.MaterialProperty.MP_NORMAL);mat.set_editor_property('tangent_space_normal',False)
    for channel,prop in [('R',unreal.MaterialProperty.MP_AMBIENT_OCCLUSION),('G',unreal.MaterialProperty.MP_ROUGHNESS),('B',unreal.MaterialProperty.MP_METALLIC)]:output(samples['arm'],channel,prop)
    lib.set_material_usage(mat,unreal.MaterialUsage.MATUSAGE_NANITE);compile_material(mat);eal.save_loaded_asset(mat,only_if_is_dirty=False)
    for key in ('Rug','RugPink'):
        old=palette[key];color=lib.get_material_instance_vector_parameter_value(old,'BaseColor');name='QualityWoven_'+key;path='/Game/Imported/Materials/'+name
        instance=unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset(name,'/Game/Imported/Materials',unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew());lib.set_material_instance_parent(instance,mat);lib.set_material_instance_vector_parameter_value(instance,'SourceTint',color);lib.update_material_instance(instance);eal.save_loaded_asset(instance,only_if_is_dirty=False);palette[key]=instance
    return {'source':lock['url'],'license':lock['license'],'normal_roughness_maps':True,'material':mat.get_path_name(),'physical_width_cm':100,'source_colors':['Rug','RugPink']}

def fit(unreal,eal,tools,actor,map_name,item,palette):
    """Fit a single border to the source rectangle, independent of mesh UV seams."""
    name='Woven_'+map_name+'_'+item['id'];path='/Game/Imported/QualityRugs/'+name;lib=unreal.MaterialEditingLibrary
    instance=unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset(name,'/Game/Imported/QualityRugs',unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
    lib.set_material_instance_parent(instance,palette[item['material']]);x,y,_=item['center_cm'];sx,sy,_=item['size_cm']
    for parameter,color in [('RugCenter',unreal.LinearColor(x,y,0,1)),('RugSize',unreal.LinearColor(sx,sy,1,1))]:
        lib.set_material_instance_vector_parameter_value(instance,parameter,color);actual=lib.get_material_instance_vector_parameter_value(instance,parameter)
        if abs(actual.r-color.r)>.01 or abs(actual.g-color.g)>.01:raise RuntimeError('Source rug bounds readback differs')
    lib.update_material_instance(instance);eal.save_loaded_asset(instance,only_if_is_dirty=False)
    for i in range(actor.static_mesh_component.get_num_materials()):actor.static_mesh_component.set_material(i,instance)
