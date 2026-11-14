#!/usr/bin/env python3
"""Package the existing game under the shared slot, background priority outside."""
import argparse,datetime,json,os,subprocess
from pathlib import Path
from engine_launch_budget import admit_engine,update
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--stage-only',action='store_true');parser.add_argument('--owner-direct',action='store_true');args=parser.parse_args()
if args.owner_direct:
    # Ashen explicitly authorized queue bypass for this local repair, Nov 14.
    update(admit='owner-authorized-direct-package-repair')
else:
    if not os.environ.get('GPU_SLOT_HELD'):raise SystemExit('Shared slot required')
    admit_engine('stage-current-development' if args.stage_only else 'package-current-development')
stamp=datetime.datetime.now(datetime.timezone.utc)
out=Path((ROOT/'out/standalone/latest.txt').read_text().strip()) if args.stage_only else ROOT/'out/standalone'/stamp.strftime('%Y%m%d-%H%M%S')
out.mkdir(parents=True,exist_ok=True)
(ROOT/'out/standalone/latest.txt').write_text(str(out)+'\n')
engine=Path(os.environ.get('UE_ROOT','/Users/Shared/Epic Games/UE_5.8'));project=ROOT/'unreal/Emerald/Emerald.uproject'
cooker='-nullrhi -unattended -nosound -NoCrashReports -DisablePython -corelimit=16 -cookprocesscount=1 -ini:Engine:[DevOptions.Shaders]:NumUnusedShaderCompilingThreads=16 -ini:Engine:[DevOptions.Shaders]:NumUnusedShaderCompilingThreadsDuringGame=16 -ini:Engine:[DevOptions.Shaders]:PercentageUnusedShaderCompilingThreads=50'
command=[str(engine/'Engine/Build/BatchFiles/RunUAT.sh'),'BuildCookRun',f'-project={project}','-noP4','-platform=Mac','-target=Emerald','-clientconfig=Development','-skipbuild','-cook','-iterate','-stage','-pak','-package','-archive',f'-archivedirectory={out}','-unattended','-utf8output','-nocompileeditor','-skipbuildeditor','-NoCodeSign','-UbtArgs=-MaxParallelActions=16','-XcodeBuildOptions=CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO -jobs 16',f'-AdditionalCookerOptions={cooker}']
if args.stage_only:
    command=[a for a in command if a not in ('-build','-cook')]+['-skipbuild','-skipcook']
prefix='stage-' if args.stage_only else ''
(out/(prefix+'request.json')).write_text(json.dumps({'started_utc':stamp.isoformat(),'configuration':'Development','jobs_max':16,'host_cores':32,'priority':'nice19/taskpolicy background','cook':'reuse completed cook' if args.stage_only else 'single process/null-RHI','command':command,'authority':'Owner explicitly requested package/smoke now during stream; one local streaming-slot exception,30fps retained; no upload/merge/submit'},indent=2)+'\n')
print('Packaging existing game at',out,flush=True)
env=os.environ.copy()
# The local unsigned app was finalized explicitly with Xcode. Avoid repeating
# its automatic-signing finalization; UBT still builds and emits the real receipt.
env['UE_BUILD_FROM_XCODE']='1'
with (out/(prefix+'uat.log')).open('w') as log:
    code=subprocess.call(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
if code==0:
    apps=list(out.glob('Mac/*.app'))
    required=[apps[0]/'Contents/UE/Emerald/Content'] if len(apps)==1 else []
    if not required or not (required[0]/'Imported/Data/littleroot.json').is_file() or any(not list((required[0]/'Paks').glob('*.'+extension)) for extension in ('pak','utoc','ucas')):
        code=2
        print('Archive is not self-contained: cooked containers/runtime JSON missing',flush=True)
(out/'package-result.json').write_text(json.dumps({'exit_code':code,'complete':code==0,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n')
raise SystemExit(code)
