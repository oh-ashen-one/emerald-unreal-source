"""Initial licensed-motion FK retarget; foot/contact and runtime QA still required."""
import json,hashlib,re
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1];EAL=unreal.EditorAssetLibrary;TOOLS=unreal.AssetToolsHelpers.get_asset_tools()
if Path(unreal.Paths.get_project_file_path()).resolve()!=ROOT/'unreal/Emerald/Emerald.uproject':raise RuntimeError('Unexpected project')
source_preparation=json.loads((ROOT/'data/character-preparation-report.json').read_text())['Casual_Male'];source_info=json.loads((ROOT/'data/native-character-import-report.json').read_text())['models']['Casual_Male'];source_file=ROOT/source_preparation['path']
if hashlib.sha256(source_file.read_bytes()).hexdigest()!=source_preparation['staged_sha256']:raise RuntimeError('Original male motion source changed')
prep={'clips':list(source_info['animations'])};source_mesh=unreal.load_asset(source_info['mesh']);objects=[unreal.load_asset(row['asset']) for row in source_info['animations'].values()]
candidate=json.loads((ROOT/'data/native-adult-character-import-report.json').read_text())
if len(candidate['meshes'])!=1:raise RuntimeError('Require complete combined adult mesh before retarget')
target_mesh=unreal.load_asset(candidate['meshes'][0]['mesh']);folder='/Game/Imported/QualityAdultRetarget';EAL.make_directory(folder)
def bones(mesh):
    component=unreal.SkeletalMeshComponent();component.set_skeletal_mesh_asset(mesh);return [str(component.get_bone_name(i)) for i in range(component.get_num_bones())]
source_bones=bones(source_mesh);target_bones=bones(target_mesh)
def resolve(names,wanted):
    norm=lambda n:re.sub('[^a-z0-9]','',n.lower());found=[n for n in names if norm(n)==norm(wanted)]
    if len(found)!=1:raise RuntimeError('Missing/ambiguous body joint '+wanted)
    return found[0]
chains=[('Spine','Hips','Torso','CC_Base_Waist','CC_Base_Spine02'),('Neck','Neck','Head','CC_Base_NeckTwist01','CC_Base_Head'),('LeftClavicle','Shoulder.L','Shoulder.L','CC_Base_L_Clavicle','CC_Base_L_Clavicle'),('RightClavicle','Shoulder.R','Shoulder.R','CC_Base_R_Clavicle','CC_Base_R_Clavicle'),('LeftArm','UpperArm.L','Fist.L','CC_Base_L_Upperarm','CC_Base_L_Hand'),('RightArm','UpperArm.R','Fist.R','CC_Base_R_Upperarm','CC_Base_R_Hand'),('LeftLeg','UpperLeg.L','LowerLeg.L','CC_Base_L_Thigh','CC_Base_L_Calf'),('RightLeg','UpperLeg.R','LowerLeg.R','CC_Base_R_Thigh','CC_Base_R_Calf'),('LeftFoot','Foot.L','Foot.L','CC_Base_L_Foot','CC_Base_L_Foot'),('RightFoot','Foot.R','Foot.R','CC_Base_R_Foot','CC_Base_R_Foot')]
def rig(name,mesh,names,root,target):
    path=folder+'/'+name;asset=unreal.load_asset(path) if EAL.does_asset_exist(path) else TOOLS.create_asset(name,folder,unreal.IKRigDefinition,unreal.IKRigDefinitionFactory());controller=unreal.IKRigController.get_controller(asset)
    if not controller.set_skeletal_mesh(mesh):raise RuntimeError('Cannot set rig reference mesh')
    for chain in list(controller.get_retarget_chains()):controller.remove_retarget_chain(chain.get_editor_property('chain_name'))
    if not controller.set_retarget_root(resolve(names,root)):raise RuntimeError('Cannot set body retarget root')
    for label,a,b,c,d in chains:
        first,last=(c,d) if target else (a,b);controller.add_retarget_chain(label,resolve(names,first),resolve(names,last),'')
    EAL.save_loaded_asset(asset,only_if_is_dirty=False);return asset
source_rig=rig('IR_QMale',source_mesh,source_bones,'Body',False);target_rig=rig('IR_Canino',target_mesh,target_bones,'CC_Base_Hip',True)
path=folder+'/RTG_QMale_Canino';rtg=unreal.load_asset(path) if EAL.does_asset_exist(path) else TOOLS.create_asset('RTG_QMale_Canino',folder,unreal.IKRetargeter,unreal.IKRetargetFactory());controller=unreal.IKRetargeterController.get_controller(rtg)
for kind,rig_asset,mesh in [(unreal.RetargetSourceOrTarget.SOURCE,source_rig,source_mesh),(unreal.RetargetSourceOrTarget.TARGET,target_rig,target_mesh)]:controller.set_ik_rig(kind,rig_asset);controller.set_preview_mesh(kind,mesh)
controller.remove_all_ops();controller.add_default_ops()
for label,*_ in chains:
    if not controller.set_source_chain(label,label):raise RuntimeError('Retarget chain mapping failed '+label)
operations=[]
for i in range(controller.get_num_retarget_ops()):
    name=str(controller.get_op_name(i));enabled='pelvis' in name.lower() or 'fk' in name.lower();controller.set_retarget_op_enabled(i,enabled);operations.append({'name':name,'enabled':enabled})
if sum(o['enabled'] for o in operations)!=2:raise RuntimeError('Expected explicit pelvis/FK initial pass, inspect op stack')
for kind in (unreal.RetargetSourceOrTarget.SOURCE,unreal.RetargetSourceOrTarget.TARGET):controller.reset_retarget_pose(controller.get_current_retarget_pose_name(kind),[],kind)
controller.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET);EAL.save_loaded_asset(rtg,only_if_is_dirty=False)
clips={}
for clip in prep['clips']:
    found=[a for a in objects if isinstance(a,unreal.AnimSequence) and a.get_name().endswith(clip)]
    if len(found)!=1:raise RuntimeError('Original motion missing/ambiguous '+clip)
    clips[clip]=found[0]
inputs=unreal.IKRetargetBatchOperationInputs()
for key,value in [('assets_to_retarget',[EAL.find_asset_data(a.get_path_name()) for a in clips.values()]),('source_mesh',source_mesh),('target_mesh',target_mesh),('ik_retarget_asset',rtg),('target_path',folder+'/Animations'),('prefix','CaninoFK_'),('include_referenced_assets',False),('overwrite_existing_files',True)]:inputs.set_editor_property(key,value)
created=unreal.IKRetargetBatchOperation.run_batch_retarget(inputs);anims={}
for clip,original in clips.items():
    found=[unreal.load_asset(str(a.package_name)) for a in created if str(a.asset_name).endswith(clip)]
    if len(found)!=1 or not isinstance(found[0],unreal.AnimSequence):raise RuntimeError('Retarget output incomplete '+clip)
    animation=found[0]
    if animation.get_editor_property('skeleton')!=target_mesh.get_editor_property('skeleton') or abs(animation.get_play_length()-original.get_play_length())>.001:raise RuntimeError('Retarget skeleton/duration mismatch')
    animation.set_editor_property('enable_root_motion',False);animation.set_editor_property('force_root_lock',True);EAL.save_loaded_asset(animation,only_if_is_dirty=False);anims[clip]={'asset':animation.get_path_name(),'duration_s':animation.get_play_length(),'original':original.get_path_name()}
EAL.save_directory(folder,only_if_is_dirty=True,recursive=True)
(ROOT/'data/native-adult-character-retarget-report.json').write_text(json.dumps({'source_mesh':source_mesh.get_path_name(),'target_mesh':target_mesh.get_path_name(),'source_bones':source_bones,'target_bones':target_bones,'chains':[c[0] for c in chains],'operations':operations,'animations':anims,'source_license':'CC0-1.0','target_license':'CC-BY-4.0','scope':'Initial pelvis/FK transfer of existing Idle/Walk/Run/SitDown, with verified matching native +Y facing and unmodified source keys. Separate root-parented source feet are mapped as independent FK chains. Native bone playback, foot contacts, modular assembly and runtime cast replacement remain unverified. No whole motion authored.','quality_gate_passed':False},indent=2)+'\n');print('Retargeted four existing CC0 clips to adult candidate; actual pose/contact QA still required')
