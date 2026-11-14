"""Owned native fixture study before lab diagnostic cells are replaced."""
import json,sys,os
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1]
if Path(unreal.Paths.get_project_file_path()).resolve()!=ROOT/'unreal/Emerald/Emerald.uproject':raise RuntimeError('Unexpected project')
sys.path.insert(0,str(ROOT/'tools'))
from quality_fixtures import prepare
EAL=unreal.EditorAssetLibrary;TOOLS=unreal.AssetToolsHelpers.get_asset_tools();LEVEL=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);ACTORS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def compile_material(mat):
    unreal.MaterialEditingLibrary.recompile_material(mat);error=unreal.EmeraldAuthoringLibrary.compile_material(mat)
    if error:raise RuntimeError('Fixture study shader compile failed: '+error)
detail_study=os.environ.get('EMERALD_DETAIL_STUDY')=='1'
report={};meshes,materials=prepare(ROOT,unreal,EAL,TOOLS,compile_material,report);path='/Game/QualityGallery/InteriorDetailStudy' if detail_study else '/Game/QualityGallery/InteriorFixtures'
if EAL.does_asset_exist(path):LEVEL.load_level(path)
elif not LEVEL.new_level(path):raise RuntimeError('Cannot create owned fixture gallery')
for actor in list(ACTORS.get_all_level_actors()):
    if actor.get_class().get_name() in ('WorldSettings','LevelScriptActor','Brush','DefaultPhysicsVolume','LevelBounds','WorldDataLayers'):continue
    if 'EmeraldGenerated' not in [str(t) for t in actor.get_editor_property('tags')]:raise RuntimeError('Unowned gallery actor preserved')
    ACTORS.destroy_actor(actor)
def spawn(cls,loc,rot=None):
    actor=ACTORS.spawn_actor_from_class(cls,unreal.Vector(*loc),rot or unreal.Rotator(pitch=0,yaw=0,roll=0));actor.set_editor_property('tags',[unreal.Name('EmeraldGenerated')]);return actor
anchor=spawn(unreal.load_class(None,'/Script/Emerald.EmeraldMapAnchor'),[0,0,0]);anchor.set_editor_property('map_id','MAP_LITTLEROOT_TOWN')
fixtures=([('fab_sink',-550,[350,270,270]),('fab_stairs',0,[200,400,330]),('potted_plant_01',600,[270,270,360])] if detail_study else [('gaming_console',-650,[260,230,80]),('electric_stove',-200,[240,240,300]),('specimen_analyzer',350,[350,350,220]),('analyzer_controller',800,[145,145,210])])
for name,x,size in fixtures:
    key='fixture_'+name;mesh=meshes[key];b=mesh.get_bounds();scale=[size[i]/(2*[b.box_extent.x,b.box_extent.y,b.box_extent.z][i]) for i in range(3)];front=-1 if name in ('specimen_analyzer','analyzer_controller') else 1;actor=spawn(unreal.StaticMeshActor,[x-front*b.origin.x*scale[0],-front*b.origin.y*scale[1],-(b.origin.z-b.box_extent.z)*scale[2]],unreal.Rotator(pitch=0,yaw=180 if front==-1 else 0,roll=0));actor.set_actor_label('Fixture_'+name);actor.set_actor_scale3d(unreal.Vector(*scale));comp=actor.static_mesh_component;comp.set_static_mesh(mesh);comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    for i,mat in enumerate(materials[key]):comp.set_material(i,mat)
    label=spawn(unreal.TextRenderActor,[x-100,190,4],unreal.Rotator(pitch=0,yaw=90,roll=0));text=label.get_component_by_class(unreal.TextRenderComponent);text.set_text(name.replace('_',' '));text.set_world_size(24.);text.set_text_render_color(unreal.Color(30,35,30,255))
floor=spawn(unreal.StaticMeshActor,[100,0,-15]);floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(unreal.Vector(23,12,.3));floor.static_mesh_component.set_material(0,unreal.load_asset('/Game/Imported/Materials/MI_Cream'));floor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
key=spawn(unreal.DirectionalLight,[0,0,1500],unreal.Rotator(pitch=-40,yaw=-45,roll=0));key.light_component.set_mobility(unreal.ComponentMobility.MOVABLE);key.light_component.set_editor_property('intensity',45000.);key.light_component.set_editor_property('light_source_angle',3.);key.light_component.set_atmosphere_sun_light(True)
spawn(unreal.SkyAtmosphere,[0,0,0]);sky=spawn(unreal.SkyLight,[0,0,1500]);sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE);sky.light_component.set_editor_property('source_type',unreal.SkyLightSourceType.SLS_CAPTURED_SCENE);sky.light_component.set_real_time_capture(True);sky.light_component.set_editor_property('intensity',1.)
volume=spawn(unreal.PostProcessVolume,[0,0,0]);volume.set_editor_property('unbound',True);settings=volume.get_editor_property('settings')
for name,value in [('auto_exposure_method',unreal.AutoExposureMethod.AEM_MANUAL),('auto_exposure_bias',0.),('auto_exposure_apply_physical_camera_exposure',True),('camera_iso',100.),('camera_shutter_speed',125.),('depth_of_field_fstop',8.)]:settings.set_editor_property('override_'+name,True);settings.set_editor_property(name,value)
volume.set_editor_property('settings',settings)
camera=spawn(unreal.CameraActor,[100,2400,950],unreal.Rotator(pitch=-18,yaw=-90,roll=0));camera.set_editor_property('auto_activate_for_player',unreal.AutoReceiveInput.PLAYER0);camera.camera_component.set_editor_property('projection_mode',unreal.CameraProjectionMode.PERSPECTIVE);camera.camera_component.set_editor_property('field_of_view',53.)
if not LEVEL.save_current_level():raise RuntimeError('Fixture gallery not saved')
(ROOT/('data/native-interior-detail-gallery-report.json' if detail_study else 'data/native-fixture-gallery-report.json')).write_text(json.dumps({'map':path,'fixtures':report['quality_fixtures'],'inspection_complete':False,'scope':'Native usable geometry/PBR readback only; visual fit/facing/quality required before source mapping','quality_gate_passed':False},indent=2)+'\n')
print('Saved owned native fixture study',path)
