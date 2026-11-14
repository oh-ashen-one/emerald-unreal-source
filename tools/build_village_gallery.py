"""Owned native gallery to inspect licensed village-kit fit before integration."""
import json,math,sys
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
EAL=unreal.EditorAssetLibrary;LEVEL=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);ACTORS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);TOOLS=unreal.AssetToolsHelpers.get_asset_tools();LIB=unreal.MaterialEditingLibrary
path='/Game/QualityGallery/VillageParts'
if EAL.does_asset_exist(path):LEVEL.load_level(path)
elif not LEVEL.new_level(path):raise RuntimeError('Cannot create owned gallery')
for actor in list(ACTORS.get_all_level_actors()):
    if actor.get_class().get_name() in ('WorldSettings','LevelScriptActor','Brush','DefaultPhysicsVolume','LevelBounds','WorldDataLayers'):continue
    if 'EmeraldGenerated' not in [str(t) for t in actor.get_editor_property('tags')]:raise RuntimeError('Unowned gallery actor preserved')
    ACTORS.destroy_actor(actor)
def spawn(cls,loc,rot=None):
    a=ACTORS.spawn_actor_from_class(cls,unreal.Vector(*loc),rot or unreal.Rotator(pitch=0,yaw=0,roll=0));a.set_editor_property('tags',[unreal.Name('EmeraldGenerated')]);return a
anchor=spawn(unreal.load_class(None,'/Script/Emerald.EmeraldMapAnchor'),[0,0,0]);anchor.set_editor_property('map_id','MAP_LITTLEROOT_TOWN')
key=spawn(unreal.DirectionalLight,[0,0,1500],unreal.Rotator(pitch=-45,yaw=-35,roll=0));key.light_component.set_mobility(unreal.ComponentMobility.MOVABLE);key.light_component.set_editor_property('intensity',45000.);key.light_component.set_atmosphere_sun_light(True)
spawn(unreal.SkyAtmosphere,[0,0,0]);sky=spawn(unreal.SkyLight,[0,0,1500]);sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE);sky.light_component.set_editor_property('source_type',unreal.SkyLightSourceType.SLS_CAPTURED_SCENE);sky.light_component.set_real_time_capture(True);sky.light_component.set_editor_property('intensity',1.)
volume=spawn(unreal.PostProcessVolume,[0,0,0]);volume.set_editor_property('unbound',True);settings=volume.get_editor_property('settings')
for name,value in [('auto_exposure_method',unreal.AutoExposureMethod.AEM_MANUAL),('auto_exposure_bias',0.),('auto_exposure_apply_physical_camera_exposure',True),('camera_iso',100.),('camera_shutter_speed',125.),('depth_of_field_fstop',8.)]:settings.set_editor_property('override_'+name,True);settings.set_editor_property(name,value)
volume.set_editor_property('settings',settings)
folder='/Game/Imported/QualityVillageMaterials';clones={};roots={}
def clone(source):
    name=source.get_path_name()
    if name in clones:return clones[name]
    target=folder+'/'+source.get_name();result=unreal.load_asset(target) if EAL.does_asset_exist(target) else EAL.duplicate_asset(name,target);clones[name]=result
    if isinstance(source,unreal.MaterialInstanceConstant):LIB.set_material_instance_parent(result,clone(source.get_editor_property('parent')));LIB.update_material_instance(result)
    elif isinstance(source,unreal.Material):roots[result.get_path_name()]=result
    else:raise RuntimeError('Unsupported source material')
    return result
base='/Game/Fantastic_Village_Pack/'
specs=[('body_v01_01','meshes/buildings/SM_BLD_body_v01_01'),('body_v02_01','meshes/buildings/SM_BLD_body_v02_01'),('door_v01','meshes/buildings/SM_BLD_door_v01_01'),('door_v02','meshes/buildings/SM_BLD_door_v02_01'),('door_v03','meshes/buildings/SM_BLD_door_v03_01'),('window_v01','meshes/buildings/SM_BLD_window_v01_01'),('window_v02','meshes/buildings/SM_BLD_window_v02_01'),('window_v07','meshes/buildings/SM_BLD_window_v07_01'),('chimney_v01','meshes/buildings/SM_BLD_chimney_v01_01'),('chimney_v02','meshes/buildings/SM_BLD_chimney_v02_01'),('sign_v01','meshes/props/deco/SM_PROP_signpost_01'),('fence_v01','meshes/props/construction/SM_PROP_fence_v01_01')]
rows=[]
for index,(label,relative) in enumerate(specs):
    mesh=unreal.load_asset(base+relative)
    if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError('Missing gallery input '+relative)
    b=mesh.get_bounds();factor=min(480/max(2*b.box_extent.x,1),480/max(2*b.box_extent.y,1),480/max(2*b.box_extent.z,1));x=(index%4)*1200;y=(index//4)*1200;yaw=0.;a=math.radians(yaw)
    loc=[x-b.origin.x*factor*math.cos(a)+b.origin.y*factor*math.sin(a),y-b.origin.x*factor*math.sin(a)-b.origin.y*factor*math.cos(a),-(b.origin.z-b.box_extent.z)*factor]
    actor=spawn(unreal.StaticMeshActor,loc,unreal.Rotator(pitch=0,yaw=yaw,roll=0));actor.set_actor_label('Gallery_'+str(index+1)+'_'+label);comp=actor.static_mesh_component;comp.set_static_mesh(mesh);actor.set_actor_scale3d(unreal.Vector(factor,factor,factor));comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    for i,slot in enumerate(mesh.get_editor_property('static_materials')):comp.set_material(i,clone(slot.material_interface))
    text=spawn(unreal.TextRenderActor,[x-240,y+350,10],unreal.Rotator(pitch=90,yaw=90,roll=0));tc=text.get_component_by_class(unreal.TextRenderComponent);tc.set_text(str(index+1)+' '+label);tc.set_world_size(52.);tc.set_text_render_color(unreal.Color(20,25,20,255))
    rows.append({'index':index+1,'label':label,'asset':mesh.get_path_name(),'native_dimensions_cm':[v*2 for v in (b.box_extent.x,b.box_extent.y,b.box_extent.z)],'triangles_lod0':mesh.get_num_triangles(0),'gallery_scale':factor,'original_materials':[s.material_interface.get_path_name() for s in mesh.get_editor_property('static_materials')]})
for material in roots.values():
    LIB.recompile_material(material);error=unreal.EmeraldAuthoringLibrary.compile_material(material)
    if error:raise RuntimeError(error)
for material in clones.values():EAL.save_loaded_asset(material,only_if_is_dirty=False)
floor=spawn(unreal.StaticMeshActor,[1800,1400,-35]);floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(unreal.Vector(56,43,.7));floor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);floor.static_mesh_component.set_material(0,unreal.load_asset('/Game/Imported/Materials/MI_Cream'))
if not LEVEL.save_current_level():raise RuntimeError('Gallery not saved')
(ROOT/'data/native-village-gallery-report.json').write_text(json.dumps({'source':'https://www.fab.com/listings/52529a12-e88e-41a0-8834-b87306f20c24','license':'Fab Standard License','map':path,'assets':rows,'integration':'Gallery only; visual fit not yet accepted'},indent=2)+'\n');print('Saved owned native village gallery:',len(rows))
