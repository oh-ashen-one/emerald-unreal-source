#!/usr/bin/env python3
"""Launch only the archived standalone and exercise its existing town inputs."""
import argparse,json,os,subprocess,time
from pathlib import Path
from engine_launch_budget import admit_engine,update
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--owner-direct',action='store_true');parser.add_argument('--stay-running',action='store_true');args=parser.parse_args()
if not args.owner_direct and not os.environ.get('GPU_SLOT_HELD'):raise SystemExit('Shared slot required')
archive=Path((ROOT/'out/standalone/latest.txt').read_text().strip());apps=list(archive.glob('Mac/*.app'))
if len(apps)!=1:raise SystemExit('Expected one archived Mac standalone app')
app=apps[0];executables=[p for p in (app/'Contents/MacOS').iterdir() if p.is_file() and os.access(p,os.X_OK)]
if len(executables)!=1:raise SystemExit('Expected one standalone executable')
if args.owner_direct:update(admit='owner-authorized-direct-standalone-smoke')
else:admit_engine('standalone-town-smoke')
out=archive/('play-smoke' if args.stay_running else 'smoke');out.mkdir(exist_ok=True);shots=out/'shots';shots.mkdir(exist_ok=True)
if args.stay_running:
    content=app/'Contents/UE/Emerald/Content'
    for extension in ('pak','utoc','ucas'):
        if not list((content/'Paks').glob('*.'+extension)):raise SystemExit('Packaged '+extension+' container missing')
    if not (content/'Imported/Data/littleroot.json').is_file():raise SystemExit('Packaged runtime JSON missing')
    command=[str(executables[0]),'-windowed','-ResX=1280','-ResY=800','-unattended','-NoCrashReports','-corelimit=16','-dpcvars=t.MaxFPS=30','-EmeraldThirdPerson','-abslog='+str(out/'engine.log'),'-ExecCmds=HighResShot 1 filename='+str(shots/'town.png')]
    (out/'request.json').write_text(json.dumps({'app':str(app),'command':command,'scope':'Visible archived standalone, normal playable town for30seconds after ready; leave game open for owner','queue_exception':'Explicit Ashen instruction November14'},indent=2)+'\n')
    with (out/'stdout.log').open('w') as log:
        process=subprocess.Popen(command,cwd=app.parent,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    ready=None;deadline=time.monotonic()+120
    while time.monotonic()<deadline:
        if process.poll() is not None:raise SystemExit('Standalone exited early: '+str(process.returncode))
        text=(out/'engine.log').read_text(errors='replace') if (out/'engine.log').exists() else ''
        if 'EMERALD_GAME ready map=MAP_LITTLEROOT_TOWN' in text:
            ready=ready or time.monotonic()
            if time.monotonic()-ready>=30:break
        time.sleep(1)
    else:raise SystemExit('Standalone did not prove30seconds in town; inspect owned PID '+str(process.pid))
    errors=[line for line in text.splitlines() if 'Fatal error:' in line or 'EMERALD_CHARACTER_LOAD_FAILED' in line or 'Failed to open descriptor' in line or 'EMERALD_DATA load failed' in line]
    if errors:raise SystemExit('Packaged runtime error; inspect local engine log')
    (out/'result.json').write_text(json.dumps({'success':True,'standalone':True,'default_town_ready':True,'alive_after_town_seconds':time.monotonic()-ready,'pid':process.pid,'left_running_for_owner':True,'app':str(app),'fps_cap':30},indent=2)+'\n')
    print('Verified standalone alive in playable town for30seconds; left running for owner, PID',process.pid)
    raise SystemExit(0)
command=[str(executables[0]),'-RenderOffScreen','-windowed','-ResX=1280','-ResY=800','-unattended','-nosound','-NoCrashReports','-corelimit=16','-dpcvars=t.MaxFPS='+os.environ.get('GPU_SLOT_FPS_CAP','30'),'-EmeraldEventSmoke','-EmeraldEventReport='+str(out/'event-result.json'),'-EmeraldEventShotDir='+str(shots),'-abslog='+str(out/'engine.log')]
(out/'request.json').write_text(json.dumps({'app':str(app),'command':command,'scope':'Actual packaged executable, default town startup and existing V/C/Esc/E/W native input scenario'},indent=2)+'\n')
with (out/'stdout.log').open('w') as log:
    process=subprocess.Popen(command,cwd=app.parent,stdout=log,stderr=subprocess.STDOUT)
    try:code=process.wait(timeout=180)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:process.wait(timeout=60)
        except subprocess.TimeoutExpired:raise SystemExit('Owned standalone stuck exiting; no relaunch')
        raise SystemExit('Standalone smoke timed out; inspect saved logs')
if code:raise SystemExit('Standalone exited '+str(code))
text=(out/'engine.log').read_text(errors='replace');event=json.loads((out/'event-result.json').read_text(encoding='utf-8-sig'))
if not event.get('success') or event.get('stage')!=5:raise SystemExit('Packaged native input smoke did not pass')
for name in ('asset-credits.png','source-town-sign.png','source-route-guard.png'):
    if not (shots/name).is_file():raise SystemExit('Packaged rendered image missing '+name)
if 'EMERALD_GAME ready map=MAP_LITTLEROOT_TOWN' not in text:raise SystemExit('Default playable town startup not proven')
if 'EMERALD_CHARACTER_LOAD_FAILED' in text or 'Fatal error:' in text:raise SystemExit('Packaged runtime asset/load error')
(out/'result.json').write_text(json.dumps({'success':True,'standalone':True,'default_town_ready':True,'native_input_scenario':event,'rendered_screenshots':True,'inspection_complete':False,'exit_code':code},indent=2)+'\n')
print('Standalone launches to playable town and packaged native inputs pass; inspect screenshots')
