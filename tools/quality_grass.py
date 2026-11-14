"""Native Quixel grass import and explicit source-channel foliage material."""
import json
from material_graph import clear_material

def prepare(root,unreal,eal,compile_material,report):
    tools=unreal.AssetToolsHelpers.get_asset_tools();lib=unreal.MaterialEditingLibrary
    folder='/Game/Imported/QualityGrass';eal.make_directory(folder)
    prepared=json.loads((root/'data/quality-grass-preparation-report.json').read_text())
    def load_or_import(file,name):
        path=folder+'/'+name+('/StaticMeshes/'+name if file.suffix=='.glb' else '')
        if not eal.does_asset_exist(path):
            task=unreal.AssetImportTask()
            for key,value in [('filename',str(file)),('destination_path',folder),('destination_name',name),('automated',True),('save',True)]:task.set_editor_property(key,value)
            tools.import_asset_tasks([task])
            if not eal.does_asset_exist(path):
                imported=[unreal.load_asset(p) for p in task.get_editor_property('imported_object_paths')]
                meshes=[a for a in imported if isinstance(a,unreal.StaticMesh)]
                if not meshes:meshes=[unreal.load_asset(p) for p in eal.list_assets(folder+'/'+name,recursive=True) if isinstance(unreal.load_asset(p),unreal.StaticMesh)]
                if len(meshes)!=1:raise RuntimeError('Grass native import did not produce one complete static mesh '+name)
                path=meshes[0].get_path_name()
        asset=unreal.load_asset(path)
        if asset is None:raise RuntimeError('Native scanned grass import missing '+name)
        return asset
    textures={}
    for label,suffix in [('Color','B-O'),('Normal','N'),('ORT','ORT')]:
        texture=load_or_import(root/'assets/source/quality-grass/Textures'/('T_wiljearqx_4K_'+suffix+'.png'),'Grass'+label)
        texture.set_editor_property('srgb',label=='Color');texture.set_editor_property('virtual_texture_streaming',False)
        texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP if label=='Normal' else (unreal.TextureCompressionSettings.TC_MASKS if label=='ORT' else unreal.TextureCompressionSettings.TC_DEFAULT))
        eal.save_loaded_asset(texture,only_if_is_dirty=False);textures[label]=texture
    path=folder+'/M_ScannedGrass';mat=unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset('M_ScannedGrass',folder,unreal.Material,unreal.MaterialFactoryNew());clear_material(mat,unreal)
    mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_MASKED);mat.set_editor_property('two_sided',True);mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE);mat.set_editor_property('opacity_mask_clip_value',.333)
    samples={}
    for label,texture in textures.items():
        node=lib.create_material_expression(mat,unreal.MaterialExpressionTextureSampleParameter2D,0,0);node.set_editor_property('parameter_name',label);node.set_editor_property('texture',texture);node.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if label=='Normal' else (unreal.MaterialSamplerType.SAMPLERTYPE_MASKS if label=='ORT' else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR));samples[label]=node
    def output(label,pin,prop):
        if not lib.connect_material_property(samples[label],pin,prop):raise RuntimeError('Grass channel binding failed '+label)
    output('Color','RGB',unreal.MaterialProperty.MP_BASE_COLOR);output('Normal','RGB',unreal.MaterialProperty.MP_NORMAL);output('ORT','R',unreal.MaterialProperty.MP_OPACITY_MASK);output('ORT','G',unreal.MaterialProperty.MP_ROUGHNESS)
    # Actual publisher ORT B is leaf translucency, not metalness or AO.
    multiply=lib.create_material_expression(mat,unreal.MaterialExpressionMultiply,0,0)
    if not lib.connect_material_expressions(samples['Color'],'RGB',multiply,'A') or not lib.connect_material_expressions(samples['ORT'],'B',multiply,'B') or not lib.connect_material_property(multiply,'',unreal.MaterialProperty.MP_SUBSURFACE_COLOR):raise RuntimeError('Grass translucency connection failed')
    lib.set_material_usage(mat,unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES);compile_material(mat);eal.save_loaded_asset(mat,only_if_is_dirty=False)
    meshes={};materials={};rows=[]
    for i,row in enumerate(prepared['variants'],1):
        mesh=load_or_import(root/row['path'],row['name'])
        nanite=mesh.get_editor_property('nanite_settings');nanite.set_editor_property('enabled',False);mesh.set_editor_property('nanite_settings',nanite);eal.save_loaded_asset(mesh,only_if_is_dirty=False)
        compile_material(mat);actual=mesh.get_num_triangles(0)
        if actual!=row['triangles']:raise RuntimeError('Grass native complete geometry differs '+row['name']+': '+str(actual)+' vs '+str(row['triangles']))
        mesh.set_material(0,mat);eal.save_loaded_asset(mesh,only_if_is_dirty=False)
        key='fab_grass_'+str(i);meshes[key]=mesh;materials[key]=[mat];bounds=mesh.get_bounds()
        rows.append(dict(name=row['name'],mesh=mesh.get_path_name(),triangles=actual,bounds_extent=[bounds.box_extent.x,bounds.box_extent.y,bounds.box_extent.z]))
    for label,texture in textures.items():
        if lib.get_material_default_texture_parameter_value(mat,label)!=texture:raise RuntimeError('Grass native texture readback differs')
    report['quality_grass']={'source':prepared['source'],'license':prepared['license'],'variants':rows,'material':mat.get_path_name(),'textures':{k:v.get_path_name() for k,v in textures.items()},'channels':{'opacity':'ORT.R','roughness':'ORT.G','translucency':'ORT.B times color','normal':'Source UE normal map'},'scope':'Eight complete source LOD0 variants, masked two-sided foliage. Original source LODs retained outside runtime; representative performance and visual acceptance remain required.'}
    (root/'data/native-quality-grass-report.json').write_text(json.dumps(report['quality_grass'],indent=2)+'\n')
    return meshes,materials
