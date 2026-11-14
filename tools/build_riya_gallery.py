"""Native attributed adult reference portrait; no gameplay cast replacement."""
import json, sys
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1];EAL=unreal.EditorAssetLibrary;LEVEL=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);ACTORS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
source_report=json.loads((ROOT/'data/native-riya-import-report.json').read_text());report={**source_report,'meshes':[r for r in source_report['meshes'] if '/Seperate_Parts/' not in r['mesh']]};path='/Game/QualityGallery/Riya'
if EAL.does_asset_exist(path):LEVEL.load_level(path)
elif not LEVEL.new_level(path):raise RuntimeError('Cannot create owned adult gallery')
for actor in list(ACTORS.get_all_level_actors()):
    if actor.get_class().get_name() in ('WorldSettings','LevelScriptActor','Brush','DefaultPhysicsVolume','LevelBounds','WorldDataLayers'):continue
    if 'EmeraldGenerated' not in [str(t) for t in actor.get_editor_property('tags')]:raise RuntimeError('Unowned gallery actor preserved')
    ACTORS.destroy_actor(actor)
def spawn(cls,loc,rot=None):
    a=ACTORS.spawn_actor_from_class(cls,unreal.Vector(*loc),rot or unreal.Rotator(pitch=0,yaw=0,roll=0));a.set_editor_property('tags',[unreal.Name('EmeraldGenerated')]);return a
anchor=spawn(unreal.load_class(None,'/Script/Emerald.EmeraldMapAnchor'),[0,0,0]);anchor.set_editor_property('map_id','MAP_LITTLEROOT_TOWN')
parents={}
for material_path in report['meshes'][0]['materials']:
    parent=unreal.load_asset(material_path)
    while isinstance(parent,unreal.MaterialInstanceConstant):parent=parent.get_editor_property('parent')
    parents[parent.get_path_name()]=parent
for parent in parents.values():
    unreal.MaterialEditingLibrary.recompile_material(parent);error=unreal.EmeraldAuthoringLibrary.compile_material(parent)
    if error:raise RuntimeError('Supplied Riya shader compilation failed: '+error)
mesh=unreal.load_asset(report['meshes'][0]['mesh']);asset_data=unreal.AssetRegistryHelpers.create_asset_data(mesh)
report['meshes'][0]['native_triangles']=unreal.AssetRegistryHelpers.get_tag_value(asset_data,'Triangles')
report['meshes'][0]['native_vertices']=unreal.AssetRegistryHelpers.get_tag_value(asset_data,'Vertices')
report['meshes'][0]['morph_targets']=[v.get_name() for v in mesh.get_editor_property('morph_targets')]
(ROOT/'data/native-riya-import-report.json').write_text(json.dumps(source_report,indent=2)+'\n')
bottom=min(m['bounds_origin'][2]-m['bounds_extent'][2] for m in report['meshes']);top=max(m['bounds_origin'][2]+m['bounds_extent'][2] for m in report['meshes']);scale=300/(top-bottom)
retarget=ROOT/'data/native-riya-retarget-report.json';motion=json.loads(retarget.read_text()) if retarget.exists() else None
supplied_path=ROOT/'data/native-riya-supplied-motion-report.json';supplied=json.loads(supplied_path.read_text()) if supplied_path.exists() else None
if motion and supplied:
    motion['animations'].update(supplied['animations'])
contact_path=ROOT/'data/native-parent-seat-correction-report.json'
if motion and contact_path.exists():
    contact=json.loads(contact_path.read_text())
    if not contact.get('source_file_unchanged') or not contact.get('non_arm_final_pose_unchanged') or not EAL.does_asset_exist(contact['asset']):raise RuntimeError('Native sourced seat contact derivative is not verified')
    motion['animations']['SitDown']={'asset':contact['asset']}
states=[('Idle',-600),('Walk',-200),('Run',200),('SitDown',600)] if motion else [('Reference',0)]
profile=None
if motion:
    if len(report['meshes'])!=1:raise RuntimeError('Complete adult assembly must be one native mesh')
    row=report['meshes'][0];mesh=unreal.load_asset(row['mesh']);source=json.loads((ROOT/'data/native-character-import-report.json').read_text())['models']['Casual_Female'];materials=[slot.get_editor_property('material_interface').get_path_name() for slot in mesh.get_editor_property('materials')]
    profile={'mesh':row['mesh'],'materials':materials,'source_joint_count':len(row['bones']),'height_cm':300,'width_scale':1,'forward_yaw':0,'probe_bone':'hand_l','animation_speed_scale':(top-bottom)/(2*source['bounds_extent'][2]),'bounds_origin':row['bounds_origin'],'bounds_extent':row['bounds_extent'],'animations':{key:value['asset'] for key,value in motion['animations'].items()}}
    if supplied:
        samples=supplied['animations']['Walk']['samples'];first,last=samples[0],samples[-1]
        speed=abs(last['bones']['pelvis'][1]-first['bones']['pelvis'][1])/(last['time_s']-first['time_s'])
        if not 100<speed<400:raise RuntimeError('Inspect supplied walk forward displacement before using cadence')
        profile['animation_speed_scale']=speed/200.
        profile['locomotion_source']='Original Fab-supplied native MF_Idle/MF_Walk_Fwd/MF_Run_Fwd, root locked in project-owned copies; CC0 retargeted SitDown retained'
    sys.path.insert(0,str(ROOT/'tools'))
    from riya_clothing_materials import adapt
    profile=adapt(unreal,ROOT,profile)
seat_bones={}
if motion:
    options=unreal.AnimPoseEvaluationOptions();options.set_editor_property('optional_skeletal_mesh',mesh)
    animation=unreal.load_asset(motion['animations']['SitDown']['asset'])
    pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(animation,max(0.,animation.get_play_length()-1./30.),options)
    if not unreal.AnimPoseExtensions.is_valid(pose):raise RuntimeError('Native seated pose evaluation failed')
    for name in ('pelvis','thigh_l','thigh_r','calf_l','calf_r','foot_l','foot_r','head'):
        p=unreal.AnimPoseExtensions.get_bone_pose(pose,name,unreal.AnimPoseSpaces.WORLD).translation
        seat_bones[name]=[p.x*scale,p.y*scale,(p.z-bottom)*scale]
    idle_pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(unreal.load_asset(profile['animations']['Idle']),0.,options)
    if not unreal.AnimPoseExtensions.is_valid(idle_pose):raise RuntimeError('Native idle pose evaluation failed')
    idle_foot_z=min(unreal.AnimPoseExtensions.get_bone_pose(idle_pose,n,unreal.AnimPoseSpaces.WORLD).translation.z for n in ('foot_l','foot_r'))
    idle_foot_height=(idle_foot_z-bottom)*scale
    profile['seated_offset_cm']=[-seat_bones['pelvis'][0],-seat_bones['pelvis'][1],idle_foot_height-min(seat_bones[n][2] for n in ('foot_l','foot_r'))]
    (ROOT/'unreal/Emerald/Content/Imported/Data/quality-riya-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
    (ROOT/'data/native-riya-profile-report.json').write_text(json.dumps({'profile':profile,'source':report['source'],'license':'Fab Standard License','scope':'Candidate descriptor with native measured visual seat offset; source-world contact and cast checks required','quality_gate_passed':False},indent=2)+'\n')
    (ROOT/'data/native-riya-seat-pose-report.json').write_text(json.dumps({'animation':animation.get_path_name(),'time_s':animation.get_play_length()-1./30.,'space':'Native evaluated component pose normalized to profile world scale, actor anchor at origin','bones_cm':seat_bones,'idle_foot_height_cm':idle_foot_height,'visual_seated_offset_cm':profile['seated_offset_cm'],'contact_verified':False},indent=2)+'\n')
for state,x in states:
    if profile:
        actor=spawn(unreal.load_class(None,'/Script/Emerald.EmeraldFigure'),[x,0,0]);actor.set_editor_property('preview_profile',json.dumps(profile,separators=(',',':')));actor.set_editor_property('preview_role','Riya'+state);actor.set_editor_property('preview_animation',unreal.load_asset(motion['animations'][state]['asset']))
    else:
        for row in report['meshes']:
            actor=spawn(unreal.SkeletalMeshActor,[0,0,-bottom*scale]);actor.set_actor_scale3d(unreal.Vector(scale,scale,scale));component=actor.get_component_by_class(unreal.SkeletalMeshComponent);component.set_skeletal_mesh_asset(unreal.load_asset(row['mesh']));component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    if state=='SitDown':
        furniture=json.loads((ROOT/'data/native-quality-furniture-import-report.json').read_text())['dining_chair_02'];chair_mesh=unreal.load_asset(furniture['mesh']);b=chair_mesh.get_bounds();sc=[110/(2*b.box_extent.x),130/(2*b.box_extent.y),250/(2*b.box_extent.z)]
        chair=spawn(unreal.StaticMeshActor,[x-b.origin.x*sc[0],-b.origin.y*sc[1],-(b.origin.z-b.box_extent.z)*sc[2]],unreal.Rotator(pitch=0,yaw=0,roll=0));chair.static_mesh_component.set_static_mesh(chair_mesh);chair.set_actor_scale3d(unreal.Vector(*sc));chair.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    if motion:
        label=spawn(unreal.TextRenderActor,[x-90,90,5],unreal.Rotator(pitch=0,yaw=90,roll=0));text=label.get_component_by_class(unreal.TextRenderComponent);text.set_text(state);text.set_world_size(45.);text.set_text_render_color(unreal.Color(30,35,30,255))
floor=spawn(unreal.StaticMeshActor,[0,0,-15]);floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(unreal.Vector(22 if motion else 6,10 if motion else 6,.3));floor.static_mesh_component.set_material(0,unreal.load_asset('/Game/Imported/Materials/MI_Cream'));floor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
key=spawn(unreal.DirectionalLight,[0,0,1500],unreal.Rotator(pitch=-40,yaw=-45,roll=0));key.light_component.set_mobility(unreal.ComponentMobility.MOVABLE);key.light_component.set_editor_property('intensity',45000.);key.light_component.set_editor_property('light_source_angle',3.);key.light_component.set_atmosphere_sun_light(True)
spawn(unreal.SkyAtmosphere,[0,0,0]);sky=spawn(unreal.SkyLight,[0,0,1500]);sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE);sky.light_component.set_editor_property('source_type',unreal.SkyLightSourceType.SLS_CAPTURED_SCENE);sky.light_component.set_real_time_capture(True);sky.light_component.set_editor_property('intensity',1.)
volume=spawn(unreal.PostProcessVolume,[0,0,0]);volume.set_editor_property('unbound',True);settings=volume.get_editor_property('settings')
for name,value in [('auto_exposure_method',unreal.AutoExposureMethod.AEM_MANUAL),('auto_exposure_bias',0.),('auto_exposure_apply_physical_camera_exposure',True),('camera_iso',100.),('camera_shutter_speed',125.),('depth_of_field_fstop',8.)]:settings.set_editor_property('override_'+name,True);settings.set_editor_property(name,value)
volume.set_editor_property('settings',settings)
camera=spawn(unreal.CameraActor,[250,1900,300] if motion else [350,700,210],unreal.Rotator(pitch=-4,yaw=-97.5,roll=0) if motion else unreal.Rotator(pitch=-4.39,yaw=-116.565,roll=0));camera.set_editor_property('auto_activate_for_player',unreal.AutoReceiveInput.PLAYER0);camera.camera_component.set_editor_property('projection_mode',unreal.CameraProjectionMode.PERSPECTIVE);camera.camera_component.set_editor_property('field_of_view',50. if motion else 42.)
credit=spawn(unreal.TextRenderActor,[-500,400,12] if motion else [-150,150,12],unreal.Rotator(pitch=0,yaw=90,roll=0));text=credit.get_component_by_class(unreal.TextRenderComponent);text.set_text('giyas3dartist | Fab Standard License\nRiya-Realistic girl\nSource + modifications: project Asset Credits');text.set_world_size(10.);text.set_text_render_color(unreal.Color(30,35,30,255))
if not LEVEL.save_current_level():raise RuntimeError('Adult gallery not saved')
(ROOT/'data/native-riya-gallery-report.json').write_text(json.dumps({'map':path,'mesh_count':len(report['meshes']),'states':[state for state,_ in states],'height_cm':300,'scale':scale,'creator':'giyas3dartist','source':report['source'],'license':'Fab Standard License','scope':'Native adult candidate assembly with optional sourced retargeted clips; settled bone/time, contacts and gameplay replacement still require verification.','quality_gate_passed':False},indent=2)+'\n');print('Saved licensed Riya native gallery')
