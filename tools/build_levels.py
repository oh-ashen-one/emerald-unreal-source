"""Run with UE's PythonScript commandlet. Rebuild six owned /Game/Maps assets.

This first pass imports licensed base assets and creates a source-tagged diagnostic
scene. Unmapped blocked cells remain visible so visual omissions cannot hide.
Runtime grid collision uses original data, independently of display-mesh bounds.
"""
import json
import sys
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1]
if Path(unreal.Paths.get_project_file_path()).resolve() != ROOT/'unreal/Emerald/Emerald.uproject':
    raise RuntimeError('Refusing to modify an unexpected project')
CONTENT=Path(unreal.Paths.project_content_dir())
DATA=json.loads((CONTENT/'Imported/Data/littleroot.json').read_text())
sys.path.insert(0,str(ROOT/'tools'))
from visual_plan import compile_plans
from material_graph import clear_material
from quality_interiors import build_map_print,build_lab_tiles
VISUAL=compile_plans(DATA)
(CONTENT/'Imported/Data/visual-plan.json').write_text(json.dumps(VISUAL,indent=2)+'\n')
LOCK=json.loads((ROOT/'data/asset-lock.json').read_text())
BAKED=json.loads((ROOT/'data/art-bake-report.json').read_text())
EAL=unreal.EditorAssetLibrary
LEVEL=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTORS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
TOOLS=unreal.AssetToolsHelpers.get_asset_tools()
def compile_native_material(material):
    # The immediate return can contain the previous resource's errors while the
    # new shader job is pending. Validate the final resource after native waits.
    unreal.MaterialEditingLibrary.recompile_material(material)
    error=unreal.EmeraldAuthoringLibrary.compile_material(material)
    if error:raise RuntimeError('Native material resource: '+error)

REPORT={'art':{},'maps':{},'presentation':'AAA quality pass candidate 1: sourced foliage and physical PBR; gate incomplete'}
# Python Rotator's native make-function positional order is not C++ FRotator's.
# Keep a native readback of that trap, and always construct with named fields.
legacy=unreal.Rotator(0,90,0)
explicit=unreal.Rotator(pitch=0,yaw=90,roll=0)
REPORT['rotation_audit']={'legacy_positional_0_90_0':{'pitch':legacy.pitch,'yaw':legacy.yaw,'roll':legacy.roll},
                          'named_yaw_90':{'pitch':explicit.pitch,'yaw':explicit.yaw,'roll':explicit.roll}}
if abs(explicit.pitch)>1e-5 or abs(explicit.yaw-90)>1e-5 or abs(explicit.roll)>1e-5:
    raise RuntimeError('Unexpected native Rotator named-field behavior')


def spawn_owned(cls,location,rotation=None):
    a=ACTORS.spawn_actor_from_class(cls,location,rotation or unreal.Rotator(pitch=0,yaw=0,roll=0))
    a.set_editor_property('tags',[unreal.Name('EmeraldGenerated')])
    return a


_PALETTE_PARENT=None


def material(name,color,roughness=.8,metallic=0):
    global _PALETTE_PARENT
    EAL.make_directory('/Game/Imported/Materials')
    if _PALETTE_PARENT is None:
        path='/Game/Imported/Materials/SourcePalette'
        _PALETTE_PARENT=unreal.load_asset(path) if EAL.does_asset_exist(path) else (EAL.duplicate_asset('/Game/Imported/Materials/Grass',path) if EAL.does_asset_exist('/Game/Imported/Materials/Grass') else TOOLS.create_asset('SourcePalette','/Game/Imported/Materials',unreal.Material,unreal.MaterialFactoryNew()))
        clear_material(_PALETTE_PARENT,unreal)
        for i,(key,value,prop) in enumerate([('BaseColor',color,unreal.MaterialProperty.MP_BASE_COLOR),('Roughness',roughness,unreal.MaterialProperty.MP_ROUGHNESS),('Metallic',metallic,unreal.MaterialProperty.MP_METALLIC)]):
            cls=unreal.MaterialExpressionVectorParameter if key=='BaseColor' else unreal.MaterialExpressionScalarParameter
            n=unreal.MaterialEditingLibrary.create_material_expression(_PALETTE_PARENT,cls,-300,i*150)
            n.set_editor_property('parameter_name',key);n.set_editor_property('group','Surface')
            n.set_editor_property('default_value',unreal.LinearColor(*value) if key=='BaseColor' else value)
            unreal.MaterialEditingLibrary.connect_material_property(n,'',prop)
        unreal.MaterialEditingLibrary.set_material_usage(_PALETTE_PARENT,unreal.MaterialUsage.MATUSAGE_NANITE)
        compile_native_material(_PALETTE_PARENT);EAL.save_loaded_asset(_PALETTE_PARENT)
    path='/Game/Imported/Materials/MI_'+name
    result=unreal.load_asset(path) if EAL.does_asset_exist(path) else TOOLS.create_asset('MI_'+name,'/Game/Imported/Materials',unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
    unreal.MaterialEditingLibrary.set_material_instance_parent(result,_PALETTE_PARENT)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(result,'BaseColor',unreal.LinearColor(*color))
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(result,'Roughness',roughness)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(result,'Metallic',metallic)
    EAL.save_loaded_asset(result)
    return result


PALETTE={name:material(name,color) for name,color in {
    'Grass':(.12,.31,.065,1),'Wood':(.51,.31,.12,1),'Wall':(.81,.79,.59,1),
    'LabFloor':(.56,.59,.47,1),'Diagnostic':(.35,.39,.43,1),
    'Rug':(.075,.29,.49,1),'Roof':(.59,.25,.075,1),'LabRoof':(.38,.44,.16,1),
    'Cream':(.85,.80,.60,1),'Trim':(.28,.19,.09,1),'Glass':(.15,.39,.49,1),
    'Door':(.42,.27,.09,1),'Sign':(.71,.75,.76,1),'Leaves':(.19,.40,.055,1),'Backdrop':(.085,.12,.10,1)}.items()}
for name,swatch in json.loads((ROOT/'data/source-style.json').read_text()).items(): PALETTE[name]=material(name,swatch['linear_rgba'])
PALETTE['Glass']=material('WindowGlass',(.018,.045,.065,1),roughness=.07)
CUBE=unreal.load_asset('/Engine/BasicShapes/Cube')
def import_surface(path,name):
    target='/Game/Imported/Surfaces/'+name
    if EAL.does_asset_exist(target): return unreal.load_asset(target)
    task=unreal.AssetImportTask()
    for field,value in [('filename',str(path)),('destination_path','/Game/Imported/Surfaces'),('destination_name',name),('automated',True),('save',True)]: task.set_editor_property(field,value)
    TOOLS.import_asset_tasks([task])
    result=unreal.load_asset(target)
    if not result: raise RuntimeError('Surface import failed '+str(path))
    return result


def build_surfaces():
    source=json.loads((ROOT/'data/pbr-lock.json').read_text())
    textures={}
    for item in source['files']:
        texture=import_surface(ROOT/item['path'],'WoodFloor_'+item['channel'])
        if item['channel']!='Diffuse': texture.set_editor_property('srgb',False)
        if item['channel']=='nor_dx': texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
        if item['channel']=='arm': texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
        EAL.save_loaded_asset(texture);textures[item['channel']]=texture
    path='/Game/Imported/Materials/WoodFloor_PBR'
    mat=unreal.load_asset(path) if EAL.does_asset_exist(path) else TOOLS.create_asset('WoodFloor_PBR','/Game/Imported/Materials',unreal.Material,unreal.MaterialFactoryNew())
    clear_material(mat,unreal)
    def node(cls,x,y): return unreal.MaterialEditingLibrary.create_material_expression(mat,cls,x,y)
    def link(a,out,b,pin):
        if not unreal.MaterialEditingLibrary.connect_material_expressions(a,out,b,pin):
            raise RuntimeError('Material connection failed: '+a.get_class().get_name()+'.'+out+' -> '+b.get_class().get_name()+'.'+pin)
    world=node(unreal.MaterialExpressionWorldPosition,-900,0)
    def channel(expression,letter,x,y):
        result=node(unreal.MaterialExpressionComponentMask,x,y)
        for ch in 'rgba':result.set_editor_property(ch,ch==letter)
        link(expression,'',result,'');return result
    wx=channel(world,'r',-900,100);wy=channel(world,'g',-900,200)
    minus=node(unreal.MaterialExpressionConstant,-1100,400);minus.set_editor_property('r',-1.)
    negx=node(unreal.MaterialExpressionMultiply,-700,100);link(wx,'',negx,'A');link(minus,'',negx,'B')
    mask=node(unreal.MaterialExpressionAppendVector,-500,0);link(wy,'',mask,'A');link(negx,'',mask,'B')
    div=node(unreal.MaterialExpressionDivide,-500,0);link(mask,'',div,'A')
    tile=node(unreal.MaterialExpressionScalarParameter,-700,-200);tile.set_editor_property('parameter_name','TileWidthCM');tile.set_editor_property('group','Surface');tile.set_editor_property('default_value',float(source['physical_width_cm']));link(tile,'',div,'B')
    normal=node(unreal.MaterialExpressionTextureSampleParameter2D,-200,300);normal.set_editor_property('texture',textures['nor_dx']);normal.set_editor_property('parameter_name','DirectXNormal');normal.set_editor_property('group','Surface');normal.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL);link(div,'',normal,'UVs')
    arm=node(unreal.MaterialExpressionTextureSampleParameter2D,-200,600);arm.set_editor_property('texture',textures['arm']);arm.set_editor_property('parameter_name','PackedARM');arm.set_editor_property('group','Surface');arm.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_MASKS);link(div,'',arm,'UVs')
    albedo=node(unreal.MaterialExpressionTextureSampleParameter2D,-200,-200)
    albedo.set_editor_property('texture',textures['Diffuse']);albedo.set_editor_property('parameter_name','Albedo');albedo.set_editor_property('group','Surface')
    link(div,'',albedo,'UVs')
    nr=channel(normal,'r',100,300);ng=channel(normal,'g',100,400);nb=channel(normal,'b',100,500)
    negy=node(unreal.MaterialExpressionMultiply,300,400);link(ng,'',negy,'A');link(minus,'',negy,'B')
    nxy=node(unreal.MaterialExpressionAppendVector,500,300);link(negy,'',nxy,'A');link(nr,'',nxy,'B')
    nworld=node(unreal.MaterialExpressionAppendVector,700,300);link(nxy,'',nworld,'A');link(nb,'',nworld,'B')
    mat.set_editor_property('tangent_space_normal',False)
    REPORT['floor_projection']={'uv_world_axes':['+Y','-X'],'normal_world_axes':['-G','R','B'],'tangent_space_normal':False,'tile_width_cm':source['physical_width_cm'],'all_maps_same_explicit_uv':True}
    for expression,pin,propname in [(albedo,'RGB',unreal.MaterialProperty.MP_BASE_COLOR),(nworld,'',unreal.MaterialProperty.MP_NORMAL),(arm,'R',unreal.MaterialProperty.MP_AMBIENT_OCCLUSION),(arm,'G',unreal.MaterialProperty.MP_ROUGHNESS),(arm,'B',unreal.MaterialProperty.MP_METALLIC)]:
        if not unreal.MaterialEditingLibrary.connect_material_property(expression,pin,propname):
            raise RuntimeError('Material output connection failed: '+str(propname)+' '+pin)
    unreal.MaterialEditingLibrary.set_material_usage(mat,unreal.MaterialUsage.MATUSAGE_NANITE)
    compile_native_material(mat);EAL.save_loaded_asset(mat)
    PALETTE['WoodFloor']=mat
    PALETTE['RegionPrint']=build_map_print(unreal,EAL,TOOLS,compile_native_material)
    path='/Game/Imported/Materials/FixtureClearGlass'
    glass=unreal.load_asset(path) if EAL.does_asset_exist(path) else TOOLS.create_asset('FixtureClearGlass','/Game/Imported/Materials',unreal.Material,unreal.MaterialFactoryNew())
    clear_material(glass,unreal)
    glass.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
    zero=unreal.MaterialEditingLibrary.create_material_expression(glass,unreal.MaterialExpressionConstant,-200,0);zero.set_editor_property('r',0.)
    for propname in (unreal.MaterialProperty.MP_OPACITY,unreal.MaterialProperty.MP_SPECULAR):
        if not unreal.MaterialEditingLibrary.connect_material_property(zero,'',propname):raise RuntimeError('Clear fixture glass graph disconnected')
    unreal.MaterialEditingLibrary.set_material_usage(glass,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH)
    compile_native_material(glass);EAL.save_loaded_asset(glass);PALETTE['FixtureClearGlass']=glass
    environment=import_surface(ROOT/source['environment']['path'],'SpruitSunrise')
    if not isinstance(environment,unreal.TextureCube): raise RuntimeError('HDR did not import as a native TextureCube')
    return environment


def build_roof_and_lab_surfaces():
    lib=unreal.MaterialEditingLibrary
    def node(mat,cls,x=0,y=0):return lib.create_material_expression(mat,cls,x,y)
    def link(a,out,b,pin):
        if not lib.connect_material_expressions(a,out,b,pin):raise RuntimeError('Surface link failed '+str(pin))
    def output(mat,n,pin,prop):
        if not lib.connect_material_property(n,pin,prop):raise RuntimeError('Surface output failed '+str(prop))
    def fresh(name):
        path='/Game/Imported/Materials/'+name
        mat=unreal.load_asset(path) if EAL.does_asset_exist(path) else TOOLS.create_asset(name,'/Game/Imported/Materials',unreal.Material,unreal.MaterialFactoryNew())
        clear_material(mat,unreal);return mat
    def scalar(mat,name,value):
        n=node(mat,unreal.MaterialExpressionScalarParameter);n.set_editor_property('parameter_name',name);n.set_editor_property('default_value',value);return n
    def mask(mat,src,pin,ch):
        n=node(mat,unreal.MaterialExpressionComponentMask)
        for c in 'rgba':n.set_editor_property(c,c==ch)
        link(src,pin,n,'');return n
    def aligned(mat,texture,size,normal=False):
        name='WorldAlignedNormal' if normal else 'WorldAlignedTexture'
        f=unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions01/Texturing/'+name)
        n=node(mat,unreal.MaterialExpressionMaterialFunctionCall);n.set_material_function(f)
        es=lib.get_material_function_expressions(f)
        ins=[str(e.get_editor_property('input_name')) for e in es if isinstance(e,unreal.MaterialExpressionFunctionInput)]
        outs=[str(e.get_editor_property('output_name')) for e in es if isinstance(e,unreal.MaterialExpressionFunctionOutput)]
        obj=node(mat,unreal.MaterialExpressionTextureObjectParameter);obj.set_editor_property('texture',texture);obj.set_editor_property('parameter_name',texture.get_name())
        link(obj,'',n,next(x for x in ins if x.lower().replace(' ','').startswith('textureobject')))
        link(size,'',n,next(x for x in ins if x.lower().replace(' ','').startswith('texturesize')))
        link(scalar(mat,'ProjectionSharpness',16.),'',n,next(x for x in ins if 'contrast' in x.lower()))
        if normal:
            flag=node(mat,unreal.MaterialExpressionStaticBool);flag.set_editor_property('value',True)
            link(flag,'',n,'WorldSpace')
        return n,next(x for x in outs if x.lower().replace(' ','').startswith('xyz') and 'flattop' not in x.lower())
    lock=json.loads((ROOT/'data/exterior-surface-lock.json').read_text());textures={}
    for item in lock['files']:
        t=import_surface(ROOT/item['path'],'RoofTile_'+item['channel'])
        if item['channel']!='Diffuse':t.set_editor_property('srgb',False)
        if item['channel']=='nor_dx':t.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
        if item['channel']=='arm':t.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
        EAL.save_loaded_asset(t);textures[item['channel']]=t
    mat=fresh('SourceRoofPBR');size=scalar(mat,'TextureWidthCM',float(lock['art_tile_width_cm']))
    color,cp=aligned(mat,textures['Diffuse'],size);norm,np=aligned(mat,textures['nor_dx'],size,True);arm,ap=aligned(mat,textures['arm'],size)
    weights=node(mat,unreal.MaterialExpressionConstant3Vector);weights.set_editor_property('constant',unreal.LinearColor(.2126,.7152,.0722,1))
    grey=node(mat,unreal.MaterialExpressionDotProduct);link(color,cp,grey,'A');link(weights,'',grey,'B')
    blend=node(mat,unreal.MaterialExpressionLinearInterpolate);link(color,cp,blend,'A');link(grey,'',blend,'B');link(scalar(mat,'Desaturate',0.),'',blend,'Alpha')
    tint=node(mat,unreal.MaterialExpressionVectorParameter);tint.set_editor_property('parameter_name','Tint');tint.set_editor_property('default_value',unreal.LinearColor(1,1,1,1))
    colored=node(mat,unreal.MaterialExpressionMultiply);link(blend,'',colored,'A');link(tint,'',colored,'B')
    output(mat,colored,'',unreal.MaterialProperty.MP_BASE_COLOR);output(mat,norm,np,unreal.MaterialProperty.MP_NORMAL)
    for c,prop in [('r',unreal.MaterialProperty.MP_AMBIENT_OCCLUSION),('g',unreal.MaterialProperty.MP_ROUGHNESS),('b',unreal.MaterialProperty.MP_METALLIC)]:output(mat,mask(mat,arm,ap,c),'',prop)
    mat.set_editor_property('tangent_space_normal',False);lib.set_material_usage(mat,unreal.MaterialUsage.MATUSAGE_NANITE);compile_native_material(mat)
    actual_width=lib.get_material_default_scalar_parameter_value(mat,'TextureWidthCM')
    if abs(actual_width-float(lock['art_tile_width_cm']))>1e-3:raise RuntimeError('Roof cached scalar differs from intended physical scale')
    EAL.save_loaded_asset(mat,only_if_is_dirty=False)
    for key,tintvalue,desat in [('Roof',(1.25,1.05,.85,1),0.),('LabRoof',(2.5,3.,1.1,1),1.)]:
        path='/Game/Imported/Materials/MI_'+key+'_PBR'
        mi=unreal.load_asset(path) if EAL.does_asset_exist(path) else TOOLS.create_asset('MI_'+key+'_PBR','/Game/Imported/Materials',unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
        lib.set_material_instance_parent(mi,mat);lib.set_material_instance_vector_parameter_value(mi,'Tint',unreal.LinearColor(*tintvalue));lib.set_material_instance_scalar_parameter_value(mi,'Desaturate',desat);EAL.save_loaded_asset(mi);PALETTE[key]=mi
    PALETTE['LabFloor']=build_lab_tiles(unreal,EAL,TOOLS,compile_native_material)
    REPORT['roof_surface']={'source':lock['source'],'texture_width_cm':lock['art_tile_width_cm'],'normal_function':'WorldAlignedNormal','world_space':True,'projection_sharpness':16}
    REPORT['lab_surface']={'source_metatile_selection':0x202,'tile_width_cm':100,'presentation':'Original procedural ceramic with beveled grout; no source bitmap','normal':'Analytic world-space bevel','roughness':'Procedural ceramic variation'}


ENVIRONMENT=build_surfaces()
build_roof_and_lab_surfaces()
from quality_surfaces import build as build_quality_surfaces
REPORT['quality_surfaces']=build_quality_surfaces(ROOT,unreal,EAL,TOOLS,import_surface,PALETTE)
from quality_ground_material import build as build_quality_ground
REPORT['quality_ground']=build_quality_ground(ROOT,unreal,EAL,TOOLS,PALETTE)
from quality_textiles import build as build_quality_textiles,fit as fit_quality_rug
REPORT['quality_textiles']=build_quality_textiles(ROOT,unreal,EAL,TOOLS,import_surface,PALETTE,compile_native_material)



def mesh_actor(mesh,loc,scale,label,mat=None,yaw=0,tags=()):
    actor=spawn_owned(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator(pitch=0,yaw=yaw,roll=0))
    actor.set_actor_label(label)
    if abs(actor.get_actor_up_vector().z-1)>1e-5:
        raise RuntimeError('Yaw-only prop unexpectedly tilted: '+label)
    component=actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    if mat: component.set_material(0,mat)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.set_editor_property('tags',[unreal.Name('EmeraldGenerated')]+[unreal.Name(t) for t in tags])
    return actor


def box(center,size,mat,label):
    return mesh_actor(CUBE,center,[v/100 for v in size],label,PALETTE[mat])


def import_art():
    assets={}
    previous_path=CONTENT/'Imported/Data/level-build-report.json'
    previous=json.loads(previous_path.read_text()).get('art',{}) if previous_path.exists() else {}
    for item in LOCK['files']:
        path=ROOT/item['path']
        if not path.exists(): raise RuntimeError('Missing acquired candidate '+str(path))
        conversion=BAKED['models'][item['name']]
        path=CONTENT/'Imported/SourceModels'/(item['name']+'_Complete.glb')
        import hashlib
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=conversion['sha256']: raise RuntimeError('Missing or modified complete assembly '+item['name'])
        old=previous.get(item['name'],{})
        if old.get('source_sha256')==item['sha256'] and old.get('converted_sha256')==conversion['sha256'] and EAL.does_asset_exist(old.get('asset','/Missing')):
            assets[item['name']]=unreal.load_asset(old['asset'])
            REPORT['art'][item['name']]=old
            continue
        task=unreal.AssetImportTask()
        task.set_editor_property('filename',str(path))
        task.set_editor_property('destination_path','/Game/Imported/Art/'+item['name'])
        task.set_editor_property('automated',True)
        task.set_editor_property('replace_existing',True)
        task.set_editor_property('save',True)
        TOOLS.import_asset_tasks([task])
        imported=[p for p in task.get_editor_property('imported_object_paths') if isinstance(unreal.load_asset(p),unreal.StaticMesh)]
        if not imported:
            imported=[p for p in EAL.list_assets('/Game/Imported/Art/'+item['name'],recursive=True) if isinstance(unreal.load_asset(p),unreal.StaticMesh) and '_Complete' in unreal.load_asset(p).get_name()]
        if len(imported)!=1: raise RuntimeError('Complete static assembly must import exactly one mesh: '+item['name']+' '+str(imported))
        assets[item['name']]=unreal.load_asset(imported[0])
        REPORT['art'][item['name']]={'asset':imported[0],'source_sha256':item['sha256'],'converted_sha256':conversion['sha256'],'source_mesh_instances':conversion['source_mesh_instances'],'conversion_schema':'static-scene-bake/1','native_import_verified':True,'render_verified':False}
    return assets


ART=import_art()
# These sub-5k-triangle licensed bases retain their complete LOD0 geometry.
# Nanite adds no geometric quality here and the importer's default triggered
# missing-usage material fallbacks in the actual game render.
for name,mesh in ART.items():
    settings=mesh.get_editor_property('nanite_settings')
    settings.set_editor_property('enabled',False)
    mesh.set_editor_property('nanite_settings',settings)
    EAL.save_loaded_asset(mesh)
    REPORT['art'][name]['nanite_enabled']=False
    REPORT['art'][name]['geometry_policy']='Complete source LOD0; no triangle reduction'


from quality_foliage import prepare as prepare_fab_foliage,scatter as scatter_fab_foliage
FAB_MESHES,FAB_MATERIALS=prepare_fab_foliage(unreal,EAL,compile_native_material,REPORT)
ART.update(FAB_MESHES)
from quality_architecture import prepare as prepare_architecture,panel_shell,place_piece
ARCH_MESHES,ARCH_MATERIALS=prepare_architecture(ROOT,unreal,EAL,TOOLS,compile_native_material,REPORT)
ART.update(ARCH_MESHES)
from quality_furniture import prepare as prepare_furniture,replacement as furniture_replacement
FURNITURE_MESHES,FURNITURE_MATERIALS=prepare_furniture(ROOT,unreal,EAL,TOOLS,compile_native_material,REPORT)
ART.update(FURNITURE_MESHES)
from quality_fixtures import prepare as prepare_fixtures
fixture_preview=json.loads((ROOT/'data/native-fixture-gallery-report.json').read_text())
if not fixture_preview.get('inspection_complete'):raise RuntimeError('Inspect native fixture study before replacing source lab diagnostics')
for candidate in json.loads((ROOT/'data/original-lab-analyzer-report.json').read_text())['assets']:
    if fixture_preview['fixtures'][candidate['id']]['converted_sha256']!=candidate['baked']['sha256']:raise RuntimeError('Original lab geometry changed; repeat native fixture inspection')
FIXTURE_MESHES,FIXTURE_MATERIALS=prepare_fixtures(ROOT,unreal,EAL,TOOLS,compile_native_material,REPORT)
ART.update(FIXTURE_MESHES);FURNITURE_MATERIALS.update(FIXTURE_MATERIALS)

def import_quality_terrain():
    path=CONTENT/'Imported/QualitySources/SourceTerrain.glb'
    if not path.is_file():raise RuntimeError('Run tools/build_quality_terrain.py first')
    task=unreal.AssetImportTask()
    for key,value in [('filename',str(path)),('destination_path','/Game/Imported/QualityTerrain'),('destination_name','SourceTerrain'),('automated',True),('save',True),('replace_existing',True)]:task.set_editor_property(key,value)
    TOOLS.import_asset_tasks([task])
    meshes=[unreal.load_asset(p) for p in task.get_editor_property('imported_object_paths') if isinstance(unreal.load_asset(p),unreal.StaticMesh)]
    if len(meshes)!=1:raise RuntimeError('Expected one complete terrain mesh')
    mesh=meshes[0];nanite=mesh.get_editor_property('nanite_settings');nanite.set_editor_property('enabled',False);mesh.set_editor_property('nanite_settings',nanite);EAL.save_loaded_asset(mesh,only_if_is_dirty=False);compile_native_material(PALETTE['Grass']);b=mesh.get_bounds()
    if abs(b.box_extent.x-14000)>2 or abs(b.box_extent.y-14000)>2 or abs(b.origin.z-b.box_extent.z)>2 or b.box_extent.z<200:raise RuntimeError('Terrain coordinates/units do not match the source seam')
    if mesh.get_num_triangles(0)!=json.loads((ROOT/'data/quality-terrain-plan.json').read_text())['triangles']:raise RuntimeError('Full terrain source geometry not retained in native LOD0')
    REPORT['quality_terrain']={'mesh':mesh.get_path_name(),'bounds_origin':[b.origin.x,b.origin.y,b.origin.z],'bounds_extent':[b.box_extent.x,b.box_extent.y,b.box_extent.z],'triangles':mesh.get_num_triangles(0),'collision':'None; context only'}
    return mesh

QUALITY_TERRAIN=import_quality_terrain()

def prop(name,x,y,sx=150,sy=150,sz=150,yaw=0,label='',z=0,mat=None):
    mesh=ART[name]
    bounds=mesh.get_bounds()
    ext=bounds.box_extent
    origin=bounds.origin
    dims=[max(2*ext.x,.001),max(2*ext.y,.001),max(2*ext.z,.001)]
    scale=[sx/dims[0],sy/dims[1],sz/dims[2]]
    # Center in XY and put mesh bottom on floor, independent of source pivot.
    import math
    ox,oy=origin.x*scale[0],origin.y*scale[1]
    a=math.radians(yaw)
    loc=[x-ox*math.cos(a)+oy*math.sin(a),y-ox*math.sin(a)-oy*math.cos(a),z-(origin.z-ext.z)*scale[2]]
    actor=mesh_actor(mesh,loc,scale,label or name,yaw=yaw)
    if mat:
        for slot in range(actor.static_mesh_component.get_num_materials()): actor.static_mesh_component.set_material(slot,PALETTE[mat])
    return actor


def lights(interior):
    key=spawn_owned(unreal.DirectionalLight,unreal.Vector(0,0,1500),unreal.Rotator(pitch=-58,yaw=-35,roll=0))
    key.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    key.light_component.set_editor_property('intensity',10000 if interior else 45000)
    key.light_component.set_editor_property('light_color',unreal.Color(255,239,211,255))
    key.light_component.set_editor_property('light_source_angle',2.5 if interior else .65)
    if not interior:key.light_component.set_atmosphere_sun_light(True)
    sky=spawn_owned(unreal.SkyLight,unreal.Vector(0,0,1800))
    sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property('source_type',unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    sky.light_component.set_editor_property('cubemap',ENVIRONMENT)
    sky.light_component.set_editor_property('intensity',20000.*10000./45000. if interior else 20000.)
    sky.light_component.set_editor_property('lower_hemisphere_is_black',False)
    REPORT.setdefault('lighting',{})['interior' if interior else 'exterior']={'key_lux':key.light_component.get_editor_property('intensity'),'hdr_gain':sky.light_component.get_editor_property('intensity'),'lower_hemisphere_is_black':sky.light_component.get_editor_property('lower_hemisphere_is_black'),'exposure':'Fixed original manual; unchanged'}
    if not interior:
        spawn_owned(unreal.SkyAtmosphere,unreal.Vector(0,0,0))
        sky.light_component.set_editor_property('source_type',unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
        sky.light_component.set_real_time_capture(True);sky.light_component.set_editor_property('intensity',1.)
        cloud=spawn_owned(unreal.VolumetricCloud,unreal.Vector(0,0,0));cc=cloud.get_component_by_class(unreal.VolumetricCloudComponent)
        cc.set_editor_property('layer_bottom_altitude',1.8);cc.set_editor_property('layer_height',3.)
        cc.set_material(unreal.load_asset('/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud_Inst'))
        fog=spawn_owned(unreal.ExponentialHeightFog,unreal.Vector(0,0,-100));fc=fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
        fc.set_editor_property('fog_density',.012);fc.set_editor_property('fog_height_falloff',.2);fc.set_editor_property('start_distance',1800.)
        fc.set_editor_property('enable_volumetric_fog',True);fc.set_editor_property('volumetric_fog_distance',20000.)
        REPORT['lighting']['exterior'].update(source_type='Atmosphere captured scene',sky_intensity=sky.light_component.get_editor_property('intensity'),hdr_gain=None,real_time_capture=True,cloud_material=cc.get_editor_property('material').get_path_name(),volumetric_fog=True)

    # Fixed exposure is part of comparable repeat captures.
    volume=spawn_owned(unreal.PostProcessVolume,unreal.Vector(0,0,0))
    volume.set_editor_property('unbound',True)
    settings=volume.get_editor_property('settings')
    settings.set_editor_property('override_auto_exposure_method',True)
    settings.set_editor_property('auto_exposure_method',unreal.AutoExposureMethod.AEM_MANUAL)
    settings.set_editor_property('override_auto_exposure_bias',True)
    settings.set_editor_property('auto_exposure_bias',0.0)
    for field,value in [('auto_exposure_apply_physical_camera_exposure',True),('camera_iso',100.0),('camera_shutter_speed',125.0),('depth_of_field_fstop',4.0 if interior else 8.0)]:
        settings.set_editor_property('override_'+field,True)
        settings.set_editor_property(field,value)
    if not interior:
        for field,value in [('color_saturation',unreal.Vector4(1.03,1.03,1.03,1)),('color_contrast',unreal.Vector4(1.03,1.03,1.03,1)),('vignette_intensity',.1)]:
            settings.set_editor_property('override_'+field,True);settings.set_editor_property(field,value)
    volume.set_editor_property('settings',settings)


def recolor(actor,rules):
    component=actor.static_mesh_component
    names=component.get_material_slot_names()
    for i in range(component.get_num_materials()):
        current=component.get_material(i)
        name=(str(names[i])+' '+(current.get_name() if current else '')).lower()
        for token,material_name in rules:
            if token in name:
                component.set_material(i,PALETTE[material_name]);break


def exterior(m):
    import random
    rng=random.Random(147)
    g=m['geometry'];cells={(c['x'],c['y']):c for c in g['cells']}
    tree_count=grass_count=0
    for (cx,cy),c in cells.items():
        x,y,mid=cx*200,cy*200,c['metatile_id']
        is_main=mid in (0x1D4,0x1D6)
        is_cut_top=mid==0x1CE and cells.get((cx,cy+1),{}).get('metatile_id') not in (0x1D4,0x1D6)
        if is_main or is_cut_top:
            key='epic_oak'
            b=ART[key].get_bounds();ratio=740/(b.box_extent.z*2)
            tree=prop(key,x+100,y+150+(200 if is_cut_top else 0),b.box_extent.x*2*ratio,b.box_extent.y*2*ratio,740,yaw=rng.uniform(-15,15),label=f"SourceTree_{cx}_{cy}")
            for index,mat in enumerate(FAB_MATERIALS[key]):tree.static_mesh_component.set_material(index,mat)
            tree_count+=1
        elif mid==3:
            place_piece(prop,ARCH_MESHES,ARCH_MATERIALS,'village_sign',x,y,140,170,f"SourceSign_{cx}_{cy}",depth=35)
            text=spawn_owned(unreal.TextRenderActor,unreal.Vector(x-52,y+25,130),unreal.Rotator(pitch=0,yaw=90,roll=0))
            tc=text.get_component_by_class(unreal.TextRenderComponent)
            script=next((e['script'] for e in m['bg_events'] if e['x']==cx and e['y']==cy),'')
            title='LITTLEROOT\nTOWN' if script.endswith('TownSign') else 'BIRCH\nLAB' if 'BirchsLabSign' in script else 'HOUSE'
            tc.set_text(title);tc.set_world_size(14.);tc.set_text_render_color(unreal.Color(230,225,204,255))
    scatter_counts=scatter_fab_foliage(unreal,spawn_owned,FAB_MESHES,FAB_MATERIALS,m,REPORT)
    grass_count=sum(n for k,n in scatter_counts.items() if k.startswith('fab_grass_'))
    # Each source building component is found from secondary metatiles and its
    # actual warp. No absolute building-center list is used.
    for i,w in enumerate(m['warp_events']):
        start=(w['x'],w['y']);component=set();pending=[start]
        while pending:
            p=pending.pop()
            if p in component or p not in cells or cells[p]['metatile_id']<0x208: continue
            component.add(p);pending.extend([(p[0]-1,p[1]),(p[0]+1,p[1]),(p[0],p[1]-1),(p[0],p[1]+1)])
        if not component: raise RuntimeError('Missing source building component')
        left,right=min(p[0] for p in component),max(p[0] for p in component)
        width=(right-left+1)*200;center_x=(left+right)*100;center_y=(w['y']-1)*200
        lab='LAB' in w['dest_map'];roof_material='LabRoof' if lab else 'Roof'
        source_windows=[p for p in sorted(component) if cells[p]['metatile_id'] in (0x23A,0x217)]
        openings=[(w['x']*200,190,0,342)]+[(p[0]*200,185,95,290) for p in source_windows]
        panel_shell(box,center_x,center_y,width,w['y']*200+100,openings)
        # Selected professional gable mesh adapted to the source building width.
        roof=prop('roofGable',center_x,center_y,width+80,760 if lab else 700,230 if lab else 320,z=380,label=f"SourceRoof_{i}")
        recolor(roof,[('roof',roof_material),('wood','Trim'),('stone','Cream')])
        for side in (-1,1):
            box([center_x+side*(width/2-10),w['y']*200+110,190],[38,38,380],'Cream',f"SourceCornerTrim_{i}_{side}")
        for p in source_windows:
            wx,wy=p[0]*200,w['y']*200+114
            box([wx,w['y']*200+94,192.5],[165,5,175],'Glass',f"SourceWindowRecess_{p[0]}_{p[1]}")
            place_piece(prop,ARCH_MESHES,ARCH_MATERIALS,'quixel_window',wx,wy,185,195,f"SourceWindowFrame_{p[0]}_{p[1]}",z=95,depth=24)
        place_piece(prop,ARCH_MESHES,ARCH_MATERIALS,'quixel_door',w['x']*200,w['y']*200+116,175,330,f"SourceDoor_{i}",depth=25)
        for side in (-1,1):box([w['x']*200+side*97,w['y']*200+119,171],[18,32,342],'Cream',f"SourceDoorTrim_{i}_{side}")
        box([w['x']*200,w['y']*200+119,342],[212,32,20],'Cream',f"SourceDoorHeader_{i}")
        box([w['x']*200,w['y']*200+148,8],[210,110,16],'WoodFloor',f"SourcePorchStep_{i}")
        if not lab:
            chimney=place_piece(prop,ARCH_MESHES,ARCH_MATERIALS,'village_chimney',center_x-width*.27,center_y-125,92,245,f"SourceChimney_{i}",z=540,depth=92)
        if lab:
            # Original vent's horizontal anchor comes from its 2x2 source motif.
            vent=next((c for c in g['cells'] if c['metatile_id']==0x242),None)
            if vent:
                vx,vy=(vent['x']+.5)*200,(vent['y']+.5)*200
                cylinder=unreal.load_asset('/Engine/BasicShapes/Cylinder')
                mesh_actor(cylinder,[vx,vy,400],[3.6,3.6,.4],'SourceVentFlange',PALETTE['Wall'])
                mesh_actor(cylinder,[vx,vy,460],[3.0,3.0,1.2],'SourceVentBody',PALETTE['Sign'])
                mesh_actor(cylinder,[vx,vy,522],[2.4,2.4,.04],'SourceVentOpening',PALETTE['Trim'])
    for fence_y in range(1000,3201,200):
        fence=prop('village_fence',4000,fence_y,200,32,125,90,label='ContextFence_'+str(fence_y))
        for index,material in enumerate(ARCH_MATERIALS['village_fence']):fence.static_mesh_component.set_material(index,material)
        fence.set_editor_property('tags',[unreal.Name('EmeraldGenerated'),unreal.Name('EmeraldBackdrop')])
    terrain=mesh_actor(QUALITY_TERRAIN,[1900,1900,0],[1,1,1],'SourceTerrainContext',PALETTE['Grass'])
    terrain.set_editor_property('tags',[unreal.Name('EmeraldGenerated'),unreal.Name('EmeraldBackdrop')])
    # Far ground remains below the contextual hills, without new gameplay cells.
    back=box([(g['width']-1)*100,(g['height']-1)*100,-180],[100000,100000,20],'Grass','FarTerrainGround')
    back.set_editor_property('tags',[unreal.Name('EmeraldGenerated'),unreal.Name('EmeraldBackdrop')])
    back.static_mesh_component.set_editor_property('cast_shadow',False)
    return {'source_building_components':len(m['warp_events']),'tree_instances':tree_count,'grass_surface_instances':grass_count}


def compound_interior(m):
    plan=VISUAL['houses' if 'House' in m['name'] else 'labs'][m['name']];g=m['geometry']
    # Single physical back wall; the source wall's two projected sprite rows
    # remain tracked in plan.wall_projection_cells, rather than repeated walls.
    box([(g['width']-1)*100,-70,185],[g['width']*200+60,80,370],'WallSiding','SourceRoomBackWall')
    box([(g['width']-1)*100,-20,30],[g['width']*200,18,60],'Trim','SourceBackSkirting')
    for side in (-1,g['width']):
        x=-110 if side==-1 else g['width']*200-90
        box([x,(g['height']-1)*100,80],[36,g['height']*200,160],'Wall','SourceSideCutaway_'+str(side))
        box([x,(g['height']-1)*100,12],[48,g['height']*200,24],'Trim','SourceSideSkirting_'+str(side))
    for item in plan['objects']:
        x,y,z=item['center_cm'];sx,sy,sz=item['size_cm']
        selected=furniture_replacement(item)
        if selected:
            key,size,yaw=selected
            actor=prop(key,x,y,*size,yaw,label=item['id'],z=z)
            for index,material in enumerate(FURNITURE_MATERIALS[key]):actor.static_mesh_component.set_material(index,material)
            continue
        actor=prop(item['asset'],x,y,sx,sy,sz,item['yaw'],label=item['id'],z=z,mat=item['material'])
        if item['asset']=='rugSquare':fit_quality_rug(unreal,EAL,TOOLS,actor,m['name'],item,PALETTE)
        if item['asset']=='chairModernCushion': recolor(actor,[('carpet','ChairGreen')])
        if item['id'].startswith('SourceDiningTable_'): recolor(actor,[('carpet','TableYellow' if 'Mays' in m['name'] else 'TablePink')])
        if item['asset'] in ('regionMapFrame','wallClock'): recolor(actor,[('_glass','FixtureClearGlass'),('_artwork','RegionPrint')])
        if item['id'].startswith('SourceBed_'): recolor(actor,[('carpetwhite','Wall'),('carpet','Rug')])
    for frame in plan['stair_frames']:
        x,y=frame['xy']
        for px,py in frame['posts']:
            box([px*200+(60 if px<x else -60),py*200,140],[40,70,280],'WallSiding',f"SourceStairFrame_{px}_{py}")
            box([px*200+(60 if px<x else -60),py*200,18],[48,78,36],'Trim',f"SourceStairPostBase_{px}_{py}")
        box([x*200,y*200,290],[350,50,20],'WallSiding',f"SourceStairLintel_{x}_{y}")
    for d in plan['diagnostics']:
        x,y=d['xy']
        box([x*200,y*200,45],[150,140,90],'Diagnostic',f"UNMAPPED_{d['metatile_id']:03X}_{x}_{y}")
    from quality_rooms import build as build_room_shell
    room=build_room_shell(ROOT,unreal,EAL,TOOLS,PALETTE,box,prop,spawn_owned,recolor,m)
    return {'mapped_prop_anchors':len(plan['objects']),
            'perspective_room_shell':room,
            'unmapped_blocked_cells':len(plan['diagnostics']),
            'source_compound_blocked_cells':len(plan['blocked_coverage']),
            'scope':plan['scope']}



EAL.make_directory('/Game/Maps')
for m in DATA['maps']:
    path='/Game/Maps/'+m['name']
    if EAL.does_asset_exist(path):
        if not LEVEL.load_level(path): raise RuntimeError('Cannot load owned generated map '+path)
        for actor in ACTORS.get_all_level_actors():
            cls=actor.get_class().get_name()
            if cls in ('WorldSettings','LevelScriptActor','Brush','DefaultPhysicsVolume','LevelBounds','WorldDataLayers'):
                continue
            if 'EmeraldGenerated' not in [str(t) for t in actor.get_editor_property('tags')]:
                raise RuntimeError('Preserving unexpected unowned actor '+actor.get_actor_label()+' in '+path)
            if not ACTORS.destroy_actor(actor): raise RuntimeError('Cannot clear generated actor '+actor.get_actor_label())
    elif not LEVEL.new_level(path):
        raise RuntimeError('Cannot create map '+path)
    anchor=spawn_owned(unreal.load_class(None,'/Script/Emerald.EmeraldMapAnchor'),unreal.Vector(0,0,0))
    anchor.set_editor_property('map_id',m['id'])
    anchor.set_actor_label('SourceMap_'+m['id'])
    g=m['geometry']; indoors=m['name']!='LittlerootTown'
    floor='LabFloor' if 'Lab' in m['name'] else ('WoodFloor' if indoors else 'Grass')
    box([(g['width']-1)*100,(g['height']-1)*100,-25],[g['width']*200,g['height']*200,50],floor,'SourceMapFloor')
    lights(indoors)
    stats=compound_interior(m) if indoors else (exterior(m) or {})
    for i,w in enumerate(m['warp_events']):
        marker=spawn_owned(unreal.TargetPoint,unreal.Vector(w['x']*200,w['y']*200,0))
        marker.set_actor_label(f"SourceWarp_{i}_to_{w['dest_map']}_{w['dest_warp_id']}")
        marker.set_editor_property('tags',[unreal.Name('EmeraldGenerated'),unreal.Name('SourceWarp'),unreal.Name(str(i))])
    if not LEVEL.save_current_level(): raise RuntimeError('Map save failed '+path)
    REPORT['maps'][m['name']]={'asset':path,'source_cells':len(g['cells']),'source_warps':len(m['warp_events']),**stats}
EAL.save_directory('/Game/Imported',only_if_is_dirty=True,recursive=True)
(CONTENT/'Imported/Data/level-build-report.json').write_text(json.dumps(REPORT,indent=2)+'\n')
unreal.log('EMERALD_LEVEL_BUILD complete '+json.dumps(REPORT['maps']))

for legacy in ('SourceRegionPrint','LabFloorPattern','LabFloorHeight'):
    path='/Game/Imported/Surfaces/'+legacy
    if EAL.does_asset_exist(path):
        refs=EAL.find_package_referencers_for_asset(path,load_assets_to_confirm=True)
        if refs:raise RuntimeError('Legacy source reference bitmap still referenced; keep quality gate closed: '+legacy)
        if not EAL.delete_asset(path):raise RuntimeError('Cannot remove legacy generated reference texture')
REPORT['runtime_source_bitmaps']=[]
(CONTENT/'Imported/Data/level-build-report.json').write_text(json.dumps(REPORT,indent=2)+'\n')
