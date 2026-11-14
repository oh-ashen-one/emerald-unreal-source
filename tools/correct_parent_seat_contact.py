"""Tail-only arm contact correction on a copy of the sourced retargeted seat."""
import hashlib,json,sys
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from contact_ik import add,sub,mul,unit,cross,dot,solve,qmul,between,rotate,slerp,length
EAL=unreal.EditorAssetLibrary;API=unreal.AnimPoseExtensions
profile=json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/quality-riya-profile.json').read_text());original_path=json.loads((ROOT/'data/native-riya-retarget-report.json').read_text())['animations']['SitDown']['asset'];original=unreal.load_asset(original_path);mesh=unreal.load_asset(profile['mesh'])
source_file=ROOT/'unreal/Emerald/Content'/Path(original_path.split('.')[0].removeprefix('/Game/')).with_suffix('.uasset');source_hash=hashlib.sha256(source_file.read_bytes()).hexdigest()
folder='/Game/Imported/QualityRiyaContacts';EAL.make_directory(folder);target=folder+'/SitDown_LapHands'
if EAL.does_asset_exist(target) and not EAL.delete_asset(target):raise RuntimeError('Cannot replace owned contact derivative')
animation=EAL.duplicate_asset(original_path,target)
if not isinstance(animation,unreal.AnimSequence):raise RuntimeError('Cannot copy source seat clip')
controller=animation.get_editor_property('controller');controller.set_model(animation.get_editor_property('data_model_interface'))
count=unreal.AnimationLibrary.get_num_keys(original);duration=original.get_play_length();options=unreal.AnimPoseEvaluationOptions();options.set_editor_property('optional_skeletal_mesh',mesh)
raw_options=unreal.AnimPoseEvaluationOptions();raw_options.set_editor_property('optional_skeletal_mesh',mesh);raw_options.set_editor_property('should_retarget',False)
scale=profile['height_cm']/(2*profile['bounds_extent'][2]);base=-(profile['bounds_origin'][2]-profile['bounds_extent'][2])*scale;offset=profile['seated_offset_cm']
targets={'l':(18.,45.,126.),'r':(-18.,45.,126.)};tracks={n:[] for side in ('l','r') for n in ('upperarm_'+side,'lowerarm_'+side,'hand_'+side)}
def xyz(v):return (v.x,v.y,v.z)
def quat(q):return (q.x,q.y,q.z,q.w)
def world(pose,bone):return API.get_bone_pose(pose,bone,unreal.AnimPoseSpaces.WORLD)
def set_world(pose,bone,position,rotation):
    old=world(pose,bone);value=unreal.Transform()
    value.set_editor_property('translation',unreal.Vector(*position));value.set_editor_property('rotation',unreal.Quat(*rotation));value.set_editor_property('scale3d',old.get_editor_property('scale3d'))
    result=API.set_bone_pose(pose,value,bone,unreal.AnimPoseSpaces.WORLD)
    return result if result is not None else pose
for frame in range(count):
    time=duration*frame/(count-1);pose=API.get_anim_pose_at_time(original,time,options);raw=API.get_anim_pose_at_time(original,time,raw_options)
    alpha=max(0.,min(1.,(frame-(count-9))/6.));alpha=alpha*alpha*(3-2*alpha)
    for side in ('l','r'):
        upper,lower,hand=('upperarm_'+side,'lowerarm_'+side,'hand_'+side);U,L,H=(world(pose,n) for n in (upper,lower,hand));a,b,c=(xyz(t.translation) for t in (U,L,H));goal=targets[side];goal=((goal[0]-offset[0])/scale,(goal[1]-offset[1])/scale,(goal[2]-base-offset[2])/scale)
        elbow,end=solve(a,b,c,goal);uq=qmul(between(sub(b,a),sub(elbow,a)),quat(U.rotation));lq=qmul(between(sub(c,b),sub(end,elbow)),quat(L.rotation))
        middle=xyz(world(pose,'middle_01_'+side).translation);index=xyz(world(pose,'index_01_'+side).translation);pinky=xyz(world(pose,'pinky_01_'+side).translation)
        forward=unit(sub(middle,c));normal=unit(cross(sub(index,c),sub(pinky,c)))
        # Index/pinky order reverses across hands; keep the anatomical back of
        # each hand up, rather than choosing a sign from the current wrist tilt.
        if side=='l':normal=mul(normal,-1)
        q1=between(forward,(0,1,0));q2=between(rotate(q1,normal),(0,0,1));hq=qmul(qmul(q2,q1),quat(H.rotation))
        pose=set_world(pose,upper,a,uq);pose=set_world(pose,lower,elbow,lq);pose=set_world(pose,hand,end,hq)
    for name in tracks:
        before=API.get_bone_pose(raw,name,unreal.AnimPoseSpaces.LOCAL);fixed=API.get_bone_pose(pose,name,unreal.AnimPoseSpaces.LOCAL)
        tracks[name].append((before.translation,unreal.Quat(*slerp(quat(before.rotation),quat(fixed.rotation),alpha)),before.get_editor_property('scale3d')))
controller.open_bracket('Sourced seat arm contact correction',False)
for name,keys in tracks.items():
    if not controller.set_bone_track_keys(name,[k[0] for k in keys],[k[1] for k in keys],[k[2] for k in keys],False):raise RuntimeError('Contact track write failed '+name)
controller.close_bracket(False);animation.set_editor_property('enable_root_motion',False);animation.set_editor_property('force_root_lock',True)
if not EAL.save_loaded_asset(animation,only_if_is_dirty=False):raise RuntimeError('Contact derivative not saved')
time=duration-1./30.;pose=API.get_anim_pose_at_time(animation,time,options);before=API.get_anim_pose_at_time(original,time,options);measured={}
for side in ('l','r'):
    p=world(pose,'hand_'+side).translation;actual=[p.x*scale+offset[0],p.y*scale+offset[1],p.z*scale+base+offset[2]]
    if length(sub(actual,targets[side]))>1.:raise RuntimeError('Native contact target readback differs '+str(actual))
    measured[side]=actual
for name in ('pelvis','foot_l','foot_r','head'):
    if length(sub(xyz(world(pose,name).translation),xyz(world(before,name).translation)))>.001:raise RuntimeError('Contact pass changed non-arm joint '+name)
if hashlib.sha256(source_file.read_bytes()).hexdigest()!=source_hash:raise RuntimeError('Original sourced animation file changed')
(ROOT/'data/native-parent-seat-correction-report.json').write_text(json.dumps({'original':original_path,'original_sha256':source_hash,'asset':animation.get_path_name(),'duration_s':duration,'num_keys':count,'modified_tracks':list(tracks),'blend':'Final eight source keys only, full correction for frozen seated frame; original translations/scales and all other tracks retained','targets_profile_cm':targets,'native_hand_readback_cm':measured,'source_file_unchanged':True,'non_arm_final_pose_unchanged':True,'scope':'Permitted arm/hand contact adaptation on existing CC0 sourced retarget, not whole motion authoring. Geometry, source anchors and gameplay untouched. Native rendered clothing/finger/cushion contact still requires inspection.','quality_gate_passed':False},indent=2)+'\n')
print('Saved sourced seat arm-contact derivative with native target readback; render inspection required')
