"""Use the creator's complete clothing PBR maps without modifying source assets."""
def adapt(unreal, root, profile):
    import json
    from material_graph import clear_material
    lib=unreal.MaterialEditingLibrary
    eal=unreal.EditorAssetLibrary
    tools=unreal.AssetToolsHelpers.get_asset_tools()
    folder='/Game/Imported/QualityRiyaMaterials'
    eal.make_directory(folder)
    rows=[]
    for index, original in enumerate(list(profile['materials'])):
        name=original.rsplit('/',1)[-1].split('.')[0]
        stem=next((v for v in ('Business_Suit','Pencil_skirt','Close_collar_short_sleeves_shirt') if name.startswith(v)),None)
        if not stem:continue
        path=folder+'/PBR_'+stem
        mat=unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset('PBR_'+stem,folder,unreal.Material,unreal.MaterialFactoryNew())
        clear_material(mat,unreal)
        bindings={};samples={}
        for suffix, prop, sampler, pin in [('Diffuse',unreal.MaterialProperty.MP_BASE_COLOR,unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,'RGB'),('Normal',unreal.MaterialProperty.MP_NORMAL,unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,'RGB'),('roughness',unreal.MaterialProperty.MP_ROUGHNESS,unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,'R')]:
            source=unreal.load_asset('/Game/Realisticgirl/Textures/'+stem+'_'+suffix)
            if not isinstance(source,unreal.Texture2D):raise RuntimeError('Missing creator clothing map '+stem+'_'+suffix)
            texture=source
            if suffix=='roughness':
                target=folder+'/T_'+stem+'_roughness'
                texture=unreal.load_asset(target) if eal.does_asset_exist(target) else eal.duplicate_asset(source.get_path_name(),target)
                texture.set_editor_property('srgb',False)
                texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
                eal.save_loaded_asset(texture,only_if_is_dirty=False)
            node=lib.create_material_expression(mat,unreal.MaterialExpressionTextureSampleParameter2D,0,0)
            node.set_editor_property('parameter_name',suffix)
            node.set_editor_property('texture',texture)
            node.set_editor_property('sampler_type',sampler)
            samples[suffix]=node
            if not lib.connect_material_property(node,pin,prop):raise RuntimeError('Clothing map disconnected')
            bindings[suffix]={'creator_source':source.get_path_name(),'assigned':texture.get_path_name()}
        # Role variants tint the creator's albedo while retaining its luminance
        # variation, normal and roughness. Default zero preserves original color.
        def node(cls):return lib.create_material_expression(mat,cls,0,0)
        def link(a,pin,b,key):
            if not lib.connect_material_expressions(a,pin,b,key):raise RuntimeError('Clothing tint input disconnected')
        tint=node(unreal.MaterialExpressionVectorParameter);tint.set_editor_property('parameter_name','ClothColor');tint.set_editor_property('default_value',unreal.LinearColor(1,1,1,1))
        amount=node(unreal.MaterialExpressionScalarParameter);amount.set_editor_property('parameter_name','ClothColorAmount');amount.set_editor_property('default_value',0.)
        weights=node(unreal.MaterialExpressionConstant3Vector);weights.set_editor_property('constant',unreal.LinearColor(.2126,.7152,.0722,1))
        luminance=node(unreal.MaterialExpressionDotProduct);link(samples['Diffuse'],'RGB',luminance,'A');link(weights,'',luminance,'B')
        detail=node(unreal.MaterialExpressionMultiply);detail.set_editor_property('const_b',.65);link(luminance,'',detail,'A')
        light=node(unreal.MaterialExpressionAdd);light.set_editor_property('const_b',.35);link(detail,'',light,'A')
        colored=node(unreal.MaterialExpressionMultiply);link(tint,'',colored,'A');link(light,'',colored,'B')
        blend=node(unreal.MaterialExpressionLinearInterpolate);link(samples['Diffuse'],'RGB',blend,'A');link(colored,'',blend,'B');link(amount,'',blend,'Alpha')
        if not lib.connect_material_property(blend,'',unreal.MaterialProperty.MP_BASE_COLOR):raise RuntimeError('Clothing tint output disconnected')
        lib.set_material_usage(mat,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH)
        lib.recompile_material(mat)
        error=unreal.EmeraldAuthoringLibrary.compile_material(mat)
        if error:raise RuntimeError('Riya clothing compile failed '+error)
        eal.save_loaded_asset(mat,only_if_is_dirty=False)
        profile['materials'][index]=mat.get_path_name()
        rows.append({'slot':index,'original':original,'assigned':mat.get_path_name(),'maps':bindings})
    if len(rows)!=3:raise RuntimeError('Expected suit, shirt and skirt clothing slots')
    (root/'data/native-riya-clothing-report.json').write_text(json.dumps({'changes':rows,'source_files_modified':False,'geometry_modified':False,'license':'Fab Standard License','scope':'Creator diffuse/normal/roughness maps explicitly connected; clothing deformation and visual acceptance remain separate','quality_gate_passed':False},indent=2)+'\n')
    return profile
