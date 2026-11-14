"""Free Fab terrain colors with licensed scan detail and source-connected wear."""
import json
from material_graph import clear_material
from quality_ground_plan import build as ground_plan,shader_mask


def build(root,unreal,eal,tools,palette):
    lib=unreal.MaterialEditingLibrary;data=json.loads((root/'unreal/Emerald/Content/Imported/Data/littleroot.json').read_text());town=next(m for m in data['maps'] if m['id']=='MAP_LITTLEROOT_TOWN');plan=ground_plan(town);(root/'data/quality-ground-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    path='/Game/Imported/Materials/QualityGroundBlend';mat=unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset('QualityGroundBlend','/Game/Imported/Materials',unreal.Material,unreal.MaterialFactoryNew());clear_material(mat,unreal)
    def node(cls):return lib.create_material_expression(mat,cls,0,0)
    def link(a,out,b,pin):
        if not lib.connect_material_expressions(a,out,b,pin):raise RuntimeError('Ground layer connection failed '+pin)
    def output(n,pin,prop):
        if not lib.connect_material_property(n,pin,prop):raise RuntimeError('Ground layer output failed')
    def scalar(name,value):
        n=node(unreal.MaterialExpressionScalarParameter);n.set_editor_property('parameter_name',name);n.set_editor_property('default_value',value);return n
    def custom(code,inputs,kind):
        n=node(unreal.MaterialExpressionCustom);n.set_editor_property('code',code);n.set_editor_property('output_type',kind);records=[]
        for name in inputs:
            item=unreal.CustomInput();item.set_editor_property('input_name',name);records.append(item)
        n.set_editor_property('inputs',records)
        for name,source in inputs.items():link(source,'',n,name)
        return n
    world=node(unreal.MaterialExpressionWorldPosition);normal=node(unreal.MaterialExpressionVertexNormalWS);xy=node(unreal.MaterialExpressionComponentMask)
    for ch in 'rgba':xy.set_editor_property(ch,ch in 'rg')
    link(world,'',xy,'')
    mask=custom(shader_mask(plan),{'P':world},unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    def uv(name,width):
        n=node(unreal.MaterialExpressionDivide);link(xy,'',n,'A');link(scalar(name,width),'',n,'B');return n
    color_uv=uv('FabColorWidthCM',256.);grass_uv=uv('GrassMicroWidthCM',200.);soil_uv=uv('SoilMicroWidthCM',130.)
    prefix='/Game/StyleHex_Studio/Shared_Resources/Free_Packs/Shared_Terrain/Shared_Terrain_Textures/Terrain_Textures_FSBF/'
    def fab_texture(name):
        source=unreal.load_asset(prefix+name)
        if source is None:raise RuntimeError('Selected free Fab ground texture missing')
        target='/Game/Imported/QualityFabTextures/'+name
        texture=unreal.load_asset(target) if eal.does_asset_exist(target) else eal.duplicate_asset(source.get_path_name(),target)
        texture.set_editor_property('virtual_texture_streaming',False);texture.set_editor_property('srgb',True);eal.save_loaded_asset(texture,only_if_is_dirty=False);return texture
    def sample(texture,key,coords,kind):
        n=node(unreal.MaterialExpressionTextureSampleParameter2D);n.set_editor_property('texture',texture);n.set_editor_property('parameter_name',key);n.set_editor_property('sampler_type',kind);link(coords,'',n,'UVs');return n
    lawn={};folder='/Game/Imported/QualityLawn';eal.make_directory(folder)
    for label in ('BaseColor','Normal','Roughness','AO'):
        path=folder+'/'+label
        if not eal.does_asset_exist(path):
            task=unreal.AssetImportTask()
            for key,value in [('filename',str(root/'assets/source/quality-lawn'/('Lawn_Grass_tkynejer_4K_'+label+'.jpg'))),('destination_path',folder),('destination_name',label),('automated',True),('save',True)]:task.set_editor_property(key,value)
            tools.import_asset_tasks([task])
        t=unreal.load_asset(path)
        if not isinstance(t,unreal.Texture2D):raise RuntimeError('Native lawn texture missing '+label)
        t.set_editor_property('srgb',label=='BaseColor');t.set_editor_property('virtual_texture_streaming',False)
        t.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP if label=='Normal' else (unreal.TextureCompressionSettings.TC_DEFAULT if label=='BaseColor' else unreal.TextureCompressionSettings.TC_MASKS));eal.save_loaded_asset(t,only_if_is_dirty=False);lawn[label]=t
    colors=[sample(lawn['BaseColor'],'FabScannedLawnColor',grass_uv,unreal.MaterialSamplerType.SAMPLERTYPE_COLOR),sample(fab_texture('T_Fsbf_Terrain_Dirt_1_BC'),'FabDirtColor',color_uv,unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)]
    normals=[];arms=[]
    for name,key,coords in [('leafy_grass','Grass',grass_uv),('brown_mud_leaves_01','Soil',soil_uv)]:
        normals.append(sample(lawn['Normal'] if key=='Grass' else unreal.load_asset('/Game/Imported/Surfaces/Quality_'+name+'_nor_dx'),key+'Normal',coords,unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL))
        arms.append(sample(unreal.load_asset('/Game/Imported/Surfaces/Quality_'+name+'_arm'),key+'ARM',coords,unreal.MaterialSamplerType.SAMPLERTYPE_MASKS))
    # Assemble actual scanned lawn AO/roughness and zero metalness explicitly.
    ao=sample(lawn['AO'],'FabScannedLawnAO',grass_uv,unreal.MaterialSamplerType.SAMPLERTYPE_MASKS);rough=sample(lawn['Roughness'],'FabScannedLawnRoughness',grass_uv,unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    ar=node(unreal.MaterialExpressionAppendVector);link(ao,'R',ar,'A');link(rough,'R',ar,'B');arm_grass=node(unreal.MaterialExpressionAppendVector);link(ar,'',arm_grass,'A');link(scalar('GrassMetallic',0.),'',arm_grass,'B')
    def mix(a,b,pin_a='RGB',pin_b='RGB'):
        n=node(unreal.MaterialExpressionLinearInterpolate);link(a,pin_a,n,'A');link(b,pin_b,n,'B');link(mask,'',n,'Alpha');return n
    color=mix(*colors);output(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
    tangent=mix(*normals);basis=custom('float3 n=normalize(N);float3 u0=abs(n.x)<.95?float3(1,0,0):float3(0,1,0);float3 u=normalize(u0-dot(u0,n)*n);float3 v=normalize(cross(n,u));return normalize(T.x*u+T.y*v+T.z*n);',{'T':tangent,'N':normal},unreal.CustomMaterialOutputType.CMOT_FLOAT3);output(basis,'',unreal.MaterialProperty.MP_NORMAL)
    arm=mix(arm_grass,arms[1],pin_a='')
    for ch,prop in [('r',unreal.MaterialProperty.MP_AMBIENT_OCCLUSION),('g',unreal.MaterialProperty.MP_ROUGHNESS),('b',unreal.MaterialProperty.MP_METALLIC)]:
        channel=node(unreal.MaterialExpressionComponentMask)
        for c in 'rgba':channel.set_editor_property(c,c==ch)
        link(arm,'',channel,'');output(channel,'',prop)
    mat.set_editor_property('tangent_space_normal',False);lib.set_material_usage(mat,unreal.MaterialUsage.MATUSAGE_NANITE);lib.recompile_material(mat);error=unreal.EmeraldAuthoringLibrary.compile_material(mat)
    if error:raise RuntimeError('Native ground layer compilation failed: '+error)
    eal.save_loaded_asset(mat,only_if_is_dirty=False);palette['Grass']=mat
    bindings={name:lib.get_material_default_texture_parameter_value(mat,name).get_path_name() for name in ('FabScannedLawnColor','GrassNormal','FabScannedLawnAO','FabScannedLawnRoughness')}
    return {'material':mat.get_path_name(),'Fab_lawn_source':'https://www.fab.com/listings/f50d1f4a-d91a-41c2-86ad-10c4ffe7f658','Fab_lawn_bindings':bindings,'Fab_dirt_color_source':'https://www.fab.com/listings/3c1a31b6-e523-4a0f-97d0-26b0db69b6bc','Fab_license':'Fab Standard License','normal_roughness_detail_sources':['https://polyhaven.com/a/brown_mud_leaves_01'],'detail_license':'CC0','lawn_physical_width_cm':200,'path_segments':len(plan['segments_cm']),'flowerbed_centers':len(plan['flower_centers_cm']),'collision':'Unchanged original source grid; visual material only'}
