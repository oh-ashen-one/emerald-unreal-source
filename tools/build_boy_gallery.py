"""Owned native portrait of every imported character part, before retargeting."""
import json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1]
EAL=unreal.EditorAssetLibrary;LEVEL=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);ACTORS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
report=json.loads((ROOT/'data/native-boy-character-import-report.json').read_text());path='/Game/QualityGallery/CharacterBoy'
for row in report['meshes']:row['materials']=[slot.get_editor_property('material_interface').get_path_name() for slot in unreal.load_asset(row['asset']).get_editor_property('materials')]
adapted=ROOT/'data/native-boy-material-adaptation-report.json'
if adapted.exists():
    for change in json.loads(adapted.read_text())['changes']:
        mesh=unreal.load_asset(change['mesh']);actual=mesh.get_editor_property('materials')[change['slot']].get_editor_property('material_interface').get_path_name()
        if actual!=change['assigned']:raise RuntimeError('Saved boy material slot differs from adapter report')
if EAL.does_asset_exist(path):LEVEL.load_level(path)
elif not LEVEL.new_level(path):raise RuntimeError('Cannot create owned character gallery')
for actor in list(ACTORS.get_all_level_actors()):
    if actor.get_class().get_name() in ('WorldSettings','LevelScriptActor','Brush','DefaultPhysicsVolume','LevelBounds','WorldDataLayers'):continue
    if 'EmeraldGenerated' not in [str(t) for t in actor.get_editor_property('tags')]:raise RuntimeError('Unowned gallery actor preserved')
    ACTORS.destroy_actor(actor)
def spawn(cls,loc,rot=None):
    actor=ACTORS.spawn_actor_from_class(cls,unreal.Vector(*loc),rot or unreal.Rotator(pitch=0,yaw=0,roll=0));actor.set_editor_property('tags',[unreal.Name('EmeraldGenerated')]);return actor
anchor=spawn(unreal.load_class(None,'/Script/Emerald.EmeraldMapAnchor'),[0,0,0]);anchor.set_editor_property('map_id','MAP_LITTLEROOT_TOWN')
top=max(m['bounds_origin'][2]+m['bounds_extent'][2] for m in report['meshes']);bottom=min(m['bounds_origin'][2]-m['bounds_extent'][2] for m in report['meshes']);scale=300/(top-bottom)
retarget_file=ROOT/'data/native-boy-character-retarget-report.json';motion=json.loads(retarget_file.read_text()) if retarget_file.exists() else None
states=[('Idle',-400),('Walk',0),('Run',400)] if motion else [('Reference',0)]
profile=None
if motion:
    primary=next(row for row in report['meshes'] if row['asset'].split('/')[-1].startswith('CC_Base_Body.'))
    low=[min(row['bounds_origin'][i]-row['bounds_extent'][i] for row in report['meshes']) for i in range(3)];high=[max(row['bounds_origin'][i]+row['bounds_extent'][i] for row in report['meshes']) for i in range(3)]
    source_info=json.loads((ROOT/'data/native-character-import-report.json').read_text())['models']['Casual_Male']
    profile={'mesh':primary['asset'],'materials':primary['materials'],'mesh_parts':[{'mesh':row['asset'],'materials':row['materials']} for row in report['meshes'] if row is not primary],'source_joint_count':report['source_joints'],'height_cm':300,'width_scale':1,'forward_yaw':0,'probe_bone':'hand_l','animation_speed_scale':(top-bottom)/(2*source_info['bounds_extent'][2]),'bounds_origin':[(a+b)*.5 for a,b in zip(low,high)],'bounds_extent':[(b-a)*.5 for a,b in zip(low,high)],'animations':{key:row['asset'] for key,row in motion['animations'].items()}}
    (ROOT/'unreal/Emerald/Content/Imported/Data/quality-boy-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
    (ROOT/'data/native-boy-character-profile-report.json').write_text(json.dumps({'profile':profile,'scope':'Candidate preview descriptor only; native modular playback/contacts/runtime integration still require verification','quality_gate_passed':False},indent=2)+'\n')
for state,x in states:
    if profile:
        actor=spawn(unreal.load_class(None,'/Script/Emerald.EmeraldFigure'),[x,0,0]);actor.set_actor_label('QualityPreview_'+state);actor.set_editor_property('preview_profile',json.dumps(profile,separators=(',',':')));actor.set_editor_property('preview_role','Boy'+state);actor.set_editor_property('preview_animation',unreal.load_asset(motion['animations'][state]['asset']))
    else:
        for i,row in enumerate(report['meshes']):
            actor=spawn(unreal.SkeletalMeshActor,[x,0,-bottom*scale]);actor.set_actor_label(state+'_CharacterPart_'+str(i));actor.set_actor_scale3d(unreal.Vector(scale,scale,scale));component=actor.get_component_by_class(unreal.SkeletalMeshComponent);component.set_skeletal_mesh_asset(unreal.load_asset(row['asset']));component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            for slot,material in enumerate(row['materials']):
                component.set_material(slot,unreal.load_asset(material))
                if component.get_material(slot).get_path_name()!=material:raise RuntimeError('Boy reference component material readback differs')
    if motion:
        label=spawn(unreal.TextRenderActor,[x-90,90,5],unreal.Rotator(pitch=0,yaw=90,roll=0));text=label.get_component_by_class(unreal.TextRenderComponent);text.set_text(state);text.set_world_size(45.);text.set_text_render_color(unreal.Color(30,35,30,255))
floor=spawn(unreal.StaticMeshActor,[0,0,-15]);floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(unreal.Vector(17 if motion else 6,10 if motion else 6,.3));floor.static_mesh_component.set_material(0,unreal.load_asset('/Game/Imported/Materials/MI_Cream'));floor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
key=spawn(unreal.DirectionalLight,[0,0,1500],unreal.Rotator(pitch=-40,yaw=-45,roll=0));key.light_component.set_mobility(unreal.ComponentMobility.MOVABLE);key.light_component.set_editor_property('intensity',45000.);key.light_component.set_editor_property('light_source_angle',3.);key.light_component.set_atmosphere_sun_light(True)
spawn(unreal.SkyAtmosphere,[0,0,0]);sky=spawn(unreal.SkyLight,[0,0,1500]);sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE);sky.light_component.set_editor_property('source_type',unreal.SkyLightSourceType.SLS_CAPTURED_SCENE);sky.light_component.set_real_time_capture(True);sky.light_component.set_editor_property('intensity',1.)
volume=spawn(unreal.PostProcessVolume,[0,0,0]);volume.set_editor_property('unbound',True);settings=volume.get_editor_property('settings')
for name,value in [('auto_exposure_method',unreal.AutoExposureMethod.AEM_MANUAL),('auto_exposure_bias',0.),('auto_exposure_apply_physical_camera_exposure',True),('camera_iso',100.),('camera_shutter_speed',125.),('depth_of_field_fstop',8.)]:settings.set_editor_property('override_'+name,True);settings.set_editor_property(name,value)
volume.set_editor_property('settings',settings)
camera=spawn(unreal.CameraActor,[250,1600,260] if motion else [350,700,210],unreal.Rotator(pitch=-3.5,yaw=-98.88,roll=0) if motion else unreal.Rotator(pitch=-4.39,yaw=-116.565,roll=0));camera.set_editor_property('auto_activate_for_player',unreal.AutoReceiveInput.PLAYER0);camera.camera_component.set_editor_property('projection_mode',unreal.CameraProjectionMode.PERSPECTIVE);camera.camera_component.set_editor_property('field_of_view',46. if motion else 42.)
if not LEVEL.save_current_level():raise RuntimeError('Portrait gallery not saved')
(ROOT/'data/native-boy-character-gallery-report.json').write_text(json.dumps({'map':path,'parts_per_figure':len(report['meshes']),'states':[s for s,_ in states],'common_skeleton':len({m['skeleton'] for m in report['meshes']})==1,'normalization_height_cm':300,'scale':scale,'camera':'Auto-activate player0 perspective; actual framing/render inspection required','scope':'Complete candidate assembly with optional initial retargeted clips. Native playback/contact and runtime cast integration still require verification.','quality_gate_passed':False},indent=2)+'\n');print('Saved complete native character gallery:',len(report['meshes']),'parts per figure')
