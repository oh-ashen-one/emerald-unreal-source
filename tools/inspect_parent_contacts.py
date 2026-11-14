"""Read native sourced seat pose and authoring APIs; do not modify animation."""
import json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1]
p=json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/quality-riya-profile.json').read_text());mesh=unreal.load_asset(p['mesh']);animation=unreal.load_asset(p['animations']['SitDown'])
options=unreal.AnimPoseEvaluationOptions();options.set_editor_property('optional_skeletal_mesh',mesh)
pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(animation,animation.get_play_length()-1./30.,options)
if not unreal.AnimPoseExtensions.is_valid(pose):raise RuntimeError('Native sourced seated pose unavailable')
component=unreal.SkeletalMeshComponent();component.set_skeletal_mesh_asset(mesh)
scale=p['height_cm']/(2*p['bounds_extent'][2]);base=-(p['bounds_origin'][2]-p['bounds_extent'][2])*scale;offset=p['seated_offset_cm'];bones={}
for name in ('pelvis','spine_05','clavicle_l','upperarm_l','lowerarm_l','hand_l','clavicle_r','upperarm_r','lowerarm_r','hand_r','thigh_l','calf_l','foot_l','thigh_r','calf_r','foot_r','head'):
    world=unreal.AnimPoseExtensions.get_bone_pose(pose,name,unreal.AnimPoseSpaces.WORLD);local=unreal.AnimPoseExtensions.get_bone_pose(pose,name,unreal.AnimPoseSpaces.LOCAL)
    pos=world.translation
    bones[name]={'parent':str(component.get_parent_bone(name)),'world_profile_cm':[pos.x*scale+offset[0],pos.y*scale+offset[1],pos.z*scale+base+offset[2]],'component_cm':[pos.x,pos.y,pos.z],'local_translation':[local.translation.x,local.translation.y,local.translation.z],'local_rotation':[local.rotation.x,local.rotation.y,local.rotation.z,local.rotation.w]}
apis={}
for key in ('controller','data_model_interface','data_model'):
    try:
        obj=animation.get_editor_property(key);apis[key]={'class':obj.get_class().get_name() if obj else None,'set_bone_track_keys':bool(obj and hasattr(obj,'set_bone_track_keys')),'get_num_keys':bool(obj and hasattr(obj,'get_number_of_keys'))}
    except Exception as error:apis[key]={'unavailable':type(error).__name__}
apis['controller_class_available']=hasattr(unreal,'AnimDataController')
(ROOT/'data/native-parent-contact-pose-report.json').write_text(json.dumps({'animation':animation.get_path_name(),'num_frames':unreal.AnimationLibrary.get_num_frames(animation),'num_keys':unreal.AnimationLibrary.get_num_keys(animation),'duration_s':animation.get_play_length(),'profile_scale':scale,'profile_offset_cm':offset,'bones':bones,'authoring_apis':apis,'scope':'Read-only native contact diagnosis of existing sourced seat pose; no keys/mesh/source anchors changed. Contact remains unaccepted.'},indent=2)+'\n')
print('Saved native sourced arm/leg contact pose and actual authoring API availability')
