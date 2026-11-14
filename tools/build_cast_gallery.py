"""Preview detailed licensed variants; never install unreviewed cast descriptors."""
import copy,json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1]
EAL=unreal.EditorAssetLibrary;LIB=unreal.MaterialEditingLibrary;TOOLS=unreal.AssetToolsHelpers.get_asset_tools()
LEVEL=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);ACTORS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
base=ROOT/'unreal/Emerald/Content/Imported/Data'
registry=json.loads((base/'character-assets.json').read_text())
profiles={name:json.loads((base/('quality-'+name+'-profile.json')).read_text()) for name in ('boy','adult')}
folder='/Game/Imported/QualityCastMaterials';EAL.make_directory(folder)
specs=[('birch','adult',(1.,1.,1.,1.)),('fat_man','adult',(.2,.45,.8,1.)),('norman','adult',(.25,.3,.32,1.)),('boy','boy',(.35,.65,.9,1.)),('sibling','boy',(.9,.35,.25,1.))]
rows=[];parameter_audit={}
for role,kind,tint in specs:
    profile=copy.deepcopy(profiles[kind])
    for key in ('height_cm','width_scale','source_graphics','source_visible_height_px'):
        if key in registry['profiles'][role]:profile[key]=registry['profiles'][role][key]
    clothing=[profile] if kind=='adult' else [p for p in profile['mesh_parts'] if 'Toon_Hoodie.' in p['mesh']]
    for part in clothing:
        indices=[13] if kind=='adult' else list(range(len(part['materials'])))
        for i in indices:
            original=unreal.load_asset(part['materials'][i]);target=folder+'/'+role+'_Shirt'
            if kind=='adult':
                # Always duplicate the verified color graph, preserving its real
                # cloth normal/roughness inputs on every regeneration.
                if EAL.does_asset_exist(target):EAL.delete_asset(target)
                mat=EAL.duplicate_asset(original.get_path_name(),target)
                source=LIB.get_material_property_input_node(mat,unreal.MaterialProperty.MP_BASE_COLOR)
                pin=LIB.get_material_property_input_node_output_name(mat,unreal.MaterialProperty.MP_BASE_COLOR)
                if source is None:raise RuntimeError('Adult shirt color graph missing')
                multiply=LIB.create_material_expression(mat,unreal.MaterialExpressionMultiply,0,0)
                color=LIB.create_material_expression(mat,unreal.MaterialExpressionVectorParameter,0,0)
                color.set_editor_property('parameter_name','RoleTint');color.set_editor_property('default_value',unreal.LinearColor(*tint))
                if not LIB.connect_material_expressions(source,pin,multiply,'A') or not LIB.connect_material_expressions(color,'',multiply,'B') or not LIB.connect_material_property(multiply,'',unreal.MaterialProperty.MP_BASE_COLOR):raise RuntimeError('Role shirt tint disconnected')
                LIB.recompile_material(mat);error=unreal.EmeraldAuthoringLibrary.compile_material(mat)
                if error:raise RuntimeError(error)
            else:
                names=[str(n) for n in LIB.get_vector_parameter_names(original)]
                parameter_audit[original.get_path_name()]=names
                parameter=next((n for n in names if n.lower() in ('basecolorfactor','basecolor','base color factor')),None)
                if parameter is None:raise RuntimeError('Inspect boy hoodie color parameters before adapting: '+str(names))
                mat=unreal.load_asset(target) if EAL.does_asset_exist(target) else TOOLS.create_asset(role+'_Shirt',folder,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
                LIB.set_material_instance_parent(mat,original);LIB.set_material_instance_vector_parameter_value(mat,parameter,unreal.LinearColor(*tint));LIB.update_material_instance(mat)
                value=LIB.get_material_instance_vector_parameter_value(mat,parameter)
                if max(abs(a-b) for a,b in zip((value.r,value.g,value.b),tint[:3]))>.0001:raise RuntimeError('Role tint native readback differs')
            EAL.save_loaded_asset(mat,only_if_is_dirty=False);part['materials'][i]=mat.get_path_name()
    profile['model']='Fab_'+kind+'_'+role
    rows.append({'role':role,'profile':profile,'base':kind,'tint':tint})
# Duplicate only our owned studio map, retaining its verified lights/sky.
path='/Game/QualityGallery/Cast'
if not EAL.does_asset_exist(path):
    if not EAL.duplicate_asset('/Game/QualityGallery/Riya',path):raise RuntimeError('Cannot copy owned studio')
if not LEVEL.load_level(path):raise RuntimeError('Cannot load owned cast studio')
for actor in list(ACTORS.get_all_level_actors()):
    cls=actor.get_class().get_name()
    if cls in ('EmeraldFigure','TextRenderActor','StaticMeshActor'):
        if 'EmeraldGenerated' not in [str(t) for t in actor.get_editor_property('tags')]:raise RuntimeError('Unowned studio actor')
        ACTORS.destroy_actor(actor)
def spawn(cls,loc,rot=None):
    a=ACTORS.spawn_actor_from_class(cls,unreal.Vector(*loc),rot or unreal.Rotator());a.set_editor_property('tags',[unreal.Name('EmeraldGenerated')]);return a
for index,row in enumerate(rows):
    x=(index-2)*330
    a=spawn(unreal.load_class(None,'/Script/Emerald.EmeraldFigure'),[x,0,0]);a.set_editor_property('preview_profile',json.dumps(row['profile'],separators=(',',':')));a.set_editor_property('preview_role','Cast_'+row['role']);a.set_editor_property('preview_animation',unreal.load_asset(row['profile']['animations']['Idle']))
    label=spawn(unreal.TextRenderActor,[x-100,100,4],unreal.Rotator(pitch=0,yaw=90,roll=0));label.text_render.set_text(row['role']);label.text_render.set_world_size(35.)
floor=spawn(unreal.StaticMeshActor,[0,0,-15]);floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(unreal.Vector(22,10,.3));floor.static_mesh_component.set_material(0,unreal.load_asset('/Game/Imported/Materials/MI_Cream'));floor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
if not LEVEL.save_current_level():raise RuntimeError('Cast studio save failed')
(base/'quality-cast-candidates.json').write_text(json.dumps({'candidates':rows},indent=2)+'\n')
(ROOT/'data/native-cast-gallery-report.json').write_text(json.dumps({'map':path,'roles':rows,'parameter_audit':parameter_audit,'installed':False,'inspection_complete':False,'quality_gate_passed':False},indent=2)+'\n')
print('Saved detailed cast candidates; world registry unchanged')
