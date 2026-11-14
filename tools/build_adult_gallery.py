"""Native attributed adult reference portrait; no gameplay cast replacement."""
import json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1];EAL=unreal.EditorAssetLibrary;LEVEL=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);ACTORS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
report=json.loads((ROOT/'data/native-adult-character-import-report.json').read_text());path='/Game/QualityGallery/AdultMan'
if EAL.does_asset_exist(path):LEVEL.load_level(path)
elif not LEVEL.new_level(path):raise RuntimeError('Cannot create owned adult gallery')
for actor in list(ACTORS.get_all_level_actors()):
    if actor.get_class().get_name() in ('WorldSettings','LevelScriptActor','Brush','DefaultPhysicsVolume','LevelBounds','WorldDataLayers'):continue
    if 'EmeraldGenerated' not in [str(t) for t in actor.get_editor_property('tags')]:raise RuntimeError('Unowned gallery actor preserved')
    ACTORS.destroy_actor(actor)
def spawn(cls,loc,rot=None):
    a=ACTORS.spawn_actor_from_class(cls,unreal.Vector(*loc),rot or unreal.Rotator(pitch=0,yaw=0,roll=0));a.set_editor_property('tags',[unreal.Name('EmeraldGenerated')]);return a
anchor=spawn(unreal.load_class(None,'/Script/Emerald.EmeraldMapAnchor'),[0,0,0]);anchor.set_editor_property('map_id','MAP_LITTLEROOT_TOWN')
bottom=min(m['bounds_origin'][2]-m['bounds_extent'][2] for m in report['meshes']);top=max(m['bounds_origin'][2]+m['bounds_extent'][2] for m in report['meshes']);scale=300/(top-bottom)
retarget=ROOT/'data/native-adult-character-retarget-report.json';motion=json.loads(retarget.read_text()) if retarget.exists() else None
states=[('Idle',-400),('Walk',0),('Run',400)] if motion else [('Reference',0)]
profile=None
if motion:
    if len(report['meshes'])!=1:raise RuntimeError('Complete adult assembly must be one native mesh')
    row=report['meshes'][0];mesh=unreal.load_asset(row['mesh']);source=json.loads((ROOT/'data/native-character-import-report.json').read_text())['models']['Casual_Male'];materials=[slot.get_editor_property('material_interface').get_path_name() for slot in mesh.get_editor_property('materials')]
    profile={'mesh':row['mesh'],'materials':materials,'source_joint_count':len(row['bones']),'height_cm':300,'width_scale':1,'forward_yaw':0,'probe_bone':'CC_Base_L_Hand','animation_speed_scale':(top-bottom)/(2*source['bounds_extent'][2]),'bounds_origin':row['bounds_origin'],'bounds_extent':row['bounds_extent'],'animations':{key:value['asset'] for key,value in motion['animations'].items()}}
    (ROOT/'unreal/Emerald/Content/Imported/Data/quality-adult-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
    (ROOT/'data/native-adult-profile-report.json').write_text(json.dumps({'profile':profile,'source':report['source'],'license':'CC-BY-4.0','scope':'Candidate descriptor only; native settled playback and cast/contact checks required','quality_gate_passed':False},indent=2)+'\n')
for state,x in states:
    if profile:
        actor=spawn(unreal.load_class(None,'/Script/Emerald.EmeraldFigure'),[x,0,0]);actor.set_editor_property('preview_profile',json.dumps(profile,separators=(',',':')));actor.set_editor_property('preview_role','Adult'+state);actor.set_editor_property('preview_animation',unreal.load_asset(motion['animations'][state]['asset']))
    else:
        for row in report['meshes']:
            actor=spawn(unreal.SkeletalMeshActor,[0,0,-bottom*scale]);actor.set_actor_scale3d(unreal.Vector(scale,scale,scale));component=actor.get_component_by_class(unreal.SkeletalMeshComponent);component.set_skeletal_mesh_asset(unreal.load_asset(row['mesh']));component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    if motion:
        label=spawn(unreal.TextRenderActor,[x-90,90,5],unreal.Rotator(pitch=0,yaw=90,roll=0));text=label.get_component_by_class(unreal.TextRenderComponent);text.set_text(state);text.set_world_size(45.);text.set_text_render_color(unreal.Color(30,35,30,255))
floor=spawn(unreal.StaticMeshActor,[0,0,-15]);floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(unreal.Vector(17 if motion else 6,10 if motion else 6,.3));floor.static_mesh_component.set_material(0,unreal.load_asset('/Game/Imported/Materials/MI_Cream'));floor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
key=spawn(unreal.DirectionalLight,[0,0,1500],unreal.Rotator(pitch=-40,yaw=-45,roll=0));key.light_component.set_mobility(unreal.ComponentMobility.MOVABLE);key.light_component.set_editor_property('intensity',45000.);key.light_component.set_editor_property('light_source_angle',3.);key.light_component.set_atmosphere_sun_light(True)
spawn(unreal.SkyAtmosphere,[0,0,0]);sky=spawn(unreal.SkyLight,[0,0,1500]);sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE);sky.light_component.set_editor_property('source_type',unreal.SkyLightSourceType.SLS_CAPTURED_SCENE);sky.light_component.set_real_time_capture(True);sky.light_component.set_editor_property('intensity',1.)
volume=spawn(unreal.PostProcessVolume,[0,0,0]);volume.set_editor_property('unbound',True);settings=volume.get_editor_property('settings')
for name,value in [('auto_exposure_method',unreal.AutoExposureMethod.AEM_MANUAL),('auto_exposure_bias',0.),('auto_exposure_apply_physical_camera_exposure',True),('camera_iso',100.),('camera_shutter_speed',125.),('depth_of_field_fstop',8.)]:settings.set_editor_property('override_'+name,True);settings.set_editor_property(name,value)
volume.set_editor_property('settings',settings)
camera=spawn(unreal.CameraActor,[250,1600,260] if motion else [350,700,210],unreal.Rotator(pitch=-3.5,yaw=-98.88,roll=0) if motion else unreal.Rotator(pitch=-4.39,yaw=-116.565,roll=0));camera.set_editor_property('auto_activate_for_player',unreal.AutoReceiveInput.PLAYER0);camera.camera_component.set_editor_property('projection_mode',unreal.CameraProjectionMode.PERSPECTIVE);camera.camera_component.set_editor_property('field_of_view',46. if motion else 42.)
credit=spawn(unreal.TextRenderActor,[-500,400,12] if motion else [-150,150,12],unreal.Rotator(pitch=0,yaw=90,roll=0));text=credit.get_component_by_class(unreal.TextRenderComponent);text.set_text('Canino3d Studio | CC BY 4.0\nFree Cartoon Game Man Character (Rigged)\nSource + license: project Asset Credits');text.set_world_size(10.);text.set_text_render_color(unreal.Color(30,35,30,255))
if not LEVEL.save_current_level():raise RuntimeError('Adult gallery not saved')
(ROOT/'data/native-adult-gallery-report.json').write_text(json.dumps({'map':path,'mesh_count':len(report['meshes']),'states':[state for state,_ in states],'height_cm':300,'scale':scale,'creator':'Canino3d Studio','source':report['source'],'license':'CC-BY-4.0','scope':'Native adult candidate assembly with optional sourced retargeted clips; settled bone/time, contacts and gameplay replacement still require verification.','quality_gate_passed':False},indent=2)+'\n');print('Saved attributed adult reference gallery')
