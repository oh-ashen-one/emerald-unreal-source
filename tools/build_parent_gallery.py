"""Source-role parent candidates on fixed chair anchors; no world installation."""
import copy,json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1];EAL=unreal.EditorAssetLibrary;LIB=unreal.MaterialEditingLibrary;TOOLS=unreal.AssetToolsHelpers.get_asset_tools()
LEVEL=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);ACTORS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
base=ROOT/'unreal/Emerald/Content/Imported/Data';source=json.loads((base/'quality-riya-profile.json').read_text());registry=json.loads((base/'character-assets.json').read_text());folder='/Game/Imported/QualityParentMaterials';EAL.make_directory(folder)
profiles={};bindings=[]
for role,color in [('mom',(.24,.065,.11,1)),('rival_mom',(.035,.09,.16,1))]:
    profile=copy.deepcopy(source)
    for key in ('height_cm','width_scale','source_graphics','source_visible_height_px'):
        if key in registry['profiles'][role]:profile[key]=registry['profiles'][role][key]
    if profile['height_cm']!=300 or profile['width_scale']!=1:raise RuntimeError('Re-evaluate seat offset for different parent dimensions')
    for index,path in enumerate(list(profile['materials'])):
        if '/QualityRiyaMaterials/PBR_' not in path:continue
        original=unreal.load_asset(path);name=role+'_'+original.get_name();target=folder+'/'+name
        mat=unreal.load_asset(target) if EAL.does_asset_exist(target) else TOOLS.create_asset(name,folder,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
        LIB.set_material_instance_parent(mat,original)
        tint=color if 'Business_Suit' in name else (.09,.025,.04,1) if 'Pencil_skirt' in name else (.85,.8,.72,1)
        amount=.8 if 'Business_Suit' in name else .35 if 'Pencil_skirt' in name else .2
        LIB.set_material_instance_vector_parameter_value(mat,'ClothColor',unreal.LinearColor(*tint));LIB.set_material_instance_scalar_parameter_value(mat,'ClothColorAmount',amount);LIB.update_material_instance(mat)
        actual=LIB.get_material_instance_vector_parameter_value(mat,'ClothColor')
        if max(abs(a-b) for a,b in zip((actual.r,actual.g,actual.b),tint[:3]))>.0001 or abs(LIB.get_material_instance_scalar_parameter_value(mat,'ClothColorAmount')-amount)>.0001:raise RuntimeError('Parent material native tint readback differs')
        maps={}
        for label in ('Diffuse','Normal','roughness'):
            texture=LIB.get_material_instance_texture_parameter_value(mat,label)
            if not texture:raise RuntimeError('Parent original PBR map missing '+label)
            maps[label]=texture.get_path_name()
        EAL.save_loaded_asset(mat,only_if_is_dirty=False);profile['materials'][index]=mat.get_path_name();bindings.append({'role':role,'slot':index,'material':mat.get_path_name(),'tint':tint,'amount':amount,'maps':maps})
    profile.update(model='Fab_Riya_'+role,appearance='Licensed original adult with role clothing tint and native measured seated visual offset; source anchor unchanged')
    profiles[role]=profile
path='/Game/QualityGallery/Parents'
if not EAL.does_asset_exist(path) and not EAL.duplicate_asset('/Game/QualityGallery/Riya',path):raise RuntimeError('Cannot copy owned parent studio')
if not LEVEL.load_level(path):raise RuntimeError('Cannot load parent studio')
for a in list(ACTORS.get_all_level_actors()):
    if a.get_class().get_name() not in ('EmeraldFigure','TextRenderActor','StaticMeshActor'):continue
    if 'EmeraldGenerated' not in [str(t) for t in a.get_editor_property('tags')]:raise RuntimeError('Unowned studio actor preserved')
    ACTORS.destroy_actor(a)
def spawn(cls,loc,rot=None):
    a=ACTORS.spawn_actor_from_class(cls,unreal.Vector(*loc),rot or unreal.Rotator());a.set_editor_property('tags',[unreal.Name('EmeraldGenerated')]);return a
states=[]
furniture=json.loads((ROOT/'data/native-quality-furniture-import-report.json').read_text())['dining_chair_02'];chair_mesh=unreal.load_asset(furniture['mesh']);b=chair_mesh.get_bounds();sc=[110/(2*b.box_extent.x),130/(2*b.box_extent.y),250/(2*b.box_extent.z)]
for i,(role,state) in enumerate((r,s) for r in profiles for s in ('Idle','Walk','SitDown')):
    x=(i-2.5)*300;profile=profiles[role];key='Parent_'+role+'_'+state
    a=spawn(unreal.load_class(None,'/Script/Emerald.EmeraldFigure'),[x,0,0]);a.set_editor_property('preview_profile',json.dumps(profile,separators=(',',':')));a.set_editor_property('preview_role',key);a.set_editor_property('preview_animation',unreal.load_asset(profile['animations'][state]))
    if state=='SitDown':
        chair=spawn(unreal.StaticMeshActor,[x-b.origin.x*sc[0],-b.origin.y*sc[1],-(b.origin.z-b.box_extent.z)*sc[2]]);chair.static_mesh_component.set_static_mesh(chair_mesh);chair.set_actor_scale3d(unreal.Vector(*sc));chair.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    label=spawn(unreal.TextRenderActor,[x-100,160,4],unreal.Rotator(pitch=0,yaw=90,roll=0));label.text_render.set_text(role+'\n'+state);label.text_render.set_world_size(30.)
    states.append({'role':role,'state':state,'preview_role':key,'actor_anchor_cm':[x,0,0],'chair_anchor_cm':[x,0,0] if state=='SitDown' else None})
floor=spawn(unreal.StaticMeshActor,[0,0,-15]);floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(unreal.Vector(25,10,.3));floor.static_mesh_component.set_material(0,unreal.load_asset('/Game/Imported/Materials/MI_Cream'));floor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
if not LEVEL.save_current_level():raise RuntimeError('Parent studio save failed')
(base/'quality-parent-candidates.json').write_text(json.dumps(profiles,indent=2)+'\n')
(ROOT/'data/native-parent-gallery-report.json').write_text(json.dumps({'map':path,'profiles':profiles,'states':states,'material_bindings':bindings,'chair_dimensions_cm':[110,130,250],'source':json.loads((ROOT/'data/fab-riya-character-lock.json').read_text()).get('url','https://www.fab.com/listings/40fcda7b-ca5b-4d0a-a8d1-eef4d79867e7'),'license':'Fab Standard License','installed':False,'inspection_complete':False,'quality_gate_passed':False,'scope':'Adult parent Idle/Walk/SitDown only; original Run deformation remains rejected. Native preview/world/contact proof required.'},indent=2)+'\n')
print('Saved two complete parent candidates with fixed source chair/actor anchors')
