"""Verify supplied sequences against the native rig and duplicate owned adapters."""
import json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1];EAL=unreal.EditorAssetLibrary
unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous(['/Game/Realisticgirl/Animation'],force_rescan=True)
mesh=unreal.load_asset('/Game/Realisticgirl/business_girl_A_pose_Pbr');skeleton=mesh.get_editor_property('skeleton');folder='/Game/Imported/QualityRiyaSuppliedMotion';EAL.make_directory(folder)
rows={}
for action,name in [('Idle','MF_Idle'),('Walk','MF_Walk_Fwd'),('Run','MF_Run_Fwd')]:
    original=unreal.load_asset('/Game/Realisticgirl/Animation/'+name)
    if not isinstance(original,unreal.AnimSequence) or original.get_editor_property('skeleton')!=skeleton:raise RuntimeError('Supplied motion does not use Riya skeleton: '+name)
    target=folder+'/'+name;animation=unreal.load_asset(target) if EAL.does_asset_exist(target) else EAL.duplicate_asset(original.get_path_name(),target)
    animation.set_editor_property('enable_root_motion',False);animation.set_editor_property('force_root_lock',True);EAL.save_loaded_asset(animation,only_if_is_dirty=False)
    options=unreal.AnimPoseEvaluationOptions();options.set_editor_property('optional_skeletal_mesh',mesh)
    samples=[]
    for i in range(16):
        time=animation.get_play_length()*i/16;pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(animation,time,options)
        if not unreal.AnimPoseExtensions.is_valid(pose):raise RuntimeError('Supplied animation pose missing')
        points={}
        for bone in ('pelvis','foot_l','foot_r','hand_l'):
            p=unreal.AnimPoseExtensions.get_bone_pose(pose,bone,unreal.AnimPoseSpaces.WORLD).translation;points[bone]=[p.x,p.y,p.z]
        samples.append({'time_s':time,'bones':points})
    rows[action]={'original':original.get_path_name(),'asset':animation.get_path_name(),'duration_s':animation.get_play_length(),'skeleton':skeleton.get_path_name(),'samples':samples}
(ROOT/'data/native-riya-supplied-motion-report.json').write_text(json.dumps({'animations':rows,'source':'data/riya-supplied-motion-source-report.json','scope':'Native sequences match the supplied112bone Riya skeleton; sampled pose data and project root-lock adapters only. Actual clothing, gait, facing, contacts and native playback require preview.','quality_gate_passed':False},indent=2)+'\n')
print('Verified three supplied Riya sequences against native skeleton; preview still required')
