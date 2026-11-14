"""Project-owned glass/display adapters for original non-Nintendo equipment."""
def adapt(root,unreal,eal,tools,compile_material,mesh,scans):
    from material_graph import clear_material
    lib=unreal.MaterialEditingLibrary;folder='/Game/Imported/QualityFixtures/OriginalLabMaterials';eal.make_directory(folder)
    parents={}
    for kind in ('Glass','Display'):
        name='M_Lab'+kind;path=folder+'/'+name
        mat=unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset(name,folder,unreal.Material,unreal.MaterialFactoryNew())
        clear_material(mat,unreal)
        if kind=='Glass':
            mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
            mat.set_editor_property('two_sided',True)
            mat.set_editor_property('translucency_lighting_mode',unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
        def node(cls):return lib.create_material_expression(mat,cls,0,0)
        def link(a,pin,b,input):
            if not lib.connect_material_expressions(a,pin,b,input):raise RuntimeError('Original lab material input disconnected')
        def output(a,pin,prop):
            if not lib.connect_material_property(a,pin,prop):raise RuntimeError('Original lab material output disconnected')
        def scalar(name,value):
            n=node(unreal.MaterialExpressionScalarParameter);n.set_editor_property('parameter_name',name);n.set_editor_property('default_value',value);return n
        def vector(name,value):
            n=node(unreal.MaterialExpressionVectorParameter);n.set_editor_property('parameter_name',name);n.set_editor_property('default_value',unreal.LinearColor(*value));return n
        samples={}
        for label,channel in [('BaseColorTexture','diff'),('NormalTexture','nor_gl'),('MetallicRoughnessTexture','arm')]:
            n=node(unreal.MaterialExpressionTextureSampleParameter2D);n.set_editor_property('parameter_name',label);n.set_editor_property('texture',scans[channel])
            if channel=='nor_gl':n.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
            elif channel=='arm':n.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
            samples[label]=n
        # Use the licensed scan only as subtle microdetail on glass/display;
        # a corroded metal albedo is inappropriate as the dominant glass color.
        variation=node(unreal.MaterialExpressionMultiply);link(samples['BaseColorTexture'],'RGB',variation,'A');link(scalar('ScanColorStrength',.025),'',variation,'B')
        color=node(unreal.MaterialExpressionAdd);link(vector('Tint',(.04,.35,.58,1) if kind=='Glass' else (.008,.035,.05,1)),'',color,'A');link(variation,'',color,'B');output(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
        normal=node(unreal.MaterialExpressionLinearInterpolate);flat=node(unreal.MaterialExpressionConstant3Vector);flat.set_editor_property('constant',unreal.LinearColor(0,0,1,1));link(flat,'',normal,'A');link(samples['NormalTexture'],'RGB',normal,'B');link(scalar('NormalStrength',.035),'',normal,'Alpha');output(normal,'',unreal.MaterialProperty.MP_NORMAL)
        rough=node(unreal.MaterialExpressionMultiply);link(samples['MetallicRoughnessTexture'],'G',rough,'A');link(scalar('ScanRoughnessStrength',.08 if kind=='Glass' else .18),'',rough,'B')
        rough_floor=node(unreal.MaterialExpressionAdd);link(rough,'',rough_floor,'A');link(scalar('RoughnessMinimum',.035 if kind=='Glass' else .12),'',rough_floor,'B');output(rough_floor,'',unreal.MaterialProperty.MP_ROUGHNESS)
        output(scalar('Metallic',0.),'',unreal.MaterialProperty.MP_METALLIC)
        if kind=='Glass':output(scalar('Opacity',.18),'',unreal.MaterialProperty.MP_OPACITY)
        else:
            emission=node(unreal.MaterialExpressionMultiply);link(vector('EmissiveColor',(.01,.12,.18,1)),'',emission,'A');link(scalar('EmissiveStrength',2000.),'',emission,'B');output(emission,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        compile_material(mat);eal.save_loaded_asset(mat,only_if_is_dirty=False);parents[kind]=mat
    slots=mesh.get_editor_property('static_materials');rows=[]
    for index,slot in enumerate(slots):
        original=slot.material_interface;name=original.get_name()
        semantic=next((key for key in ('ViewingDome','StatusLight','Display') if key in name),None)
        if semantic is None:continue
        name='MI_Lab'+semantic;path=folder+'/'+name
        mi=unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset(name,folder,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
        lib.set_material_instance_parent(mi,parents['Glass' if semantic=='ViewingDome' else 'Display'])
        for key,channel in [('BaseColorTexture','diff'),('NormalTexture','nor_gl'),('MetallicRoughnessTexture','arm')]:
            lib.set_material_instance_texture_parameter_value(mi,key,scans[channel])
            if lib.get_material_instance_texture_parameter_value(mi,key)!=scans[channel]:raise RuntimeError('Lab detail texture binding differs')
        if semantic=='StatusLight':
            lib.set_material_instance_vector_parameter_value(mi,'EmissiveColor',unreal.LinearColor(.08,.7,.85,1));lib.set_material_instance_scalar_parameter_value(mi,'EmissiveStrength',500.)
        value=lib.get_material_instance_scalar_parameter_value(mi,'Opacity' if semantic=='ViewingDome' else 'EmissiveStrength')
        expected=.18 if semantic=='ViewingDome' else 500. if semantic=='StatusLight' else 2000.
        if abs(value-expected)>1e-4:raise RuntimeError('Original lab scalar adapter readback differs')
        lib.update_material_instance(mi);eal.save_loaded_asset(mi,only_if_is_dirty=False)
        slot.material_interface=mi;slots[index]=slot;rows.append({'slot':index,'semantic':semantic,'material':mi.get_path_name(),'parent':mi.get_editor_property('parent').get_path_name(),'emissive_strength':lib.get_material_instance_scalar_parameter_value(mi,'EmissiveStrength') if semantic!='ViewingDome' else None,'opacity':lib.get_material_instance_scalar_parameter_value(mi,'Opacity') if semantic=='ViewingDome' else None})
    mesh.set_editor_property('static_materials',slots);eal.save_loaded_asset(mesh,only_if_is_dirty=False)
    actual=mesh.get_editor_property('static_materials')
    if any(actual[row['slot']].material_interface.get_path_name()!=row['material'] for row in rows):raise RuntimeError('Original lab static material slots did not persist')
    return rows
