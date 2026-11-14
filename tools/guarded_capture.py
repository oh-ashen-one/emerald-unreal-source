#!/usr/bin/env python3
"""Owned offscreen game capture with a first-image watchdog, beneath gpu_slot."""
import json
import os
import re
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
if not os.environ.get('GPU_SLOT_HELD'):
    raise SystemExit('Run tools/render_baseline.sh through the shared guard')
mode=sys.argv[2] if len(sys.argv)>2 else 'baseline'
if mode not in ('baseline','events','lighting','wander','quality','perspective','camera_edges','gallery','motion','contacts'):raise SystemExit('Unknown capture scenario')
output=Path(sys.argv[1]).resolve()
output.mkdir(parents=True,exist_ok=True)
start_map=sys.argv[3] if mode in ('gallery','motion','contacts') and len(sys.argv)>3 else '/Game/Maps/LittlerootTown'
if mode in ('gallery','motion','contacts') and not re.fullmatch(r'/Game/QualityGallery/[A-Za-z0-9_]+',start_map):raise SystemExit('Unexpected gallery map')
if mode=='contacts' and start_map not in ('/Game/QualityGallery/ParentBrendanRoom','/Game/QualityGallery/ParentMayRoom'):raise SystemExit('Unexpected source contact map')
if mode=='motion' and start_map!='/Game/QualityGallery/Parents':raise SystemExit('Motion QA currently requires owned parent gallery')
engine=Path(os.environ.get('UE_ROOT','/Users/Shared/Epic Games/UE_5.8'))
command=[str(engine/'Engine/Binaries/Mac/UnrealEditor-Cmd'),str(ROOT/'unreal/Emerald/Emerald.uproject'),
         start_map,'-game','-RenderOffScreen','-unattended','-nosound','-nosplash','-NoCrashReports','-DisablePython',
         '-ResX=1280','-ResY=800','-windowed','-dpcvars=t.MaxFPS='+os.environ.get('GPU_SLOT_FPS_CAP','60'),
         '-EmeraldCaptureDir='+str(output/'shots'),'-abslog='+str(output/'engine.log')]
if mode in ('baseline','wander','quality','perspective','camera_edges'):command+=['-EmeraldCaptureCharacters']
if mode=='wander':command+=['-EmeraldCaptureWander']
if mode in ('quality','perspective','camera_edges'):
    command=[arg+',r.TextureStreaming=0' if arg.startswith('-dpcvars=') else arg for arg in command]
    command+=['-ExecCmds=r.TextureStreaming,r.DynamicGlobalIlluminationMethod,r.ReflectionMethod,r.Lumen.DiffuseIndirect.Allow,r.Lumen.Reflections.Allow']
    command+=['-EmeraldQualityViews','-EmeraldQualityCameraLock='+str(ROOT/'data/quality-camera-lock.json')] if mode=='quality' else ['-EmeraldCapturePerspective']
if mode=='camera_edges':command+=['-EmeraldCaptureCameraEdges']
sky_gains=[1] if mode in ('gallery','motion','contacts') else [1,100,1000,5000]
if mode in ('lighting','gallery','motion','contacts'):
    value='1' if mode in ('gallery','motion','contacts') else sys.argv[3] if len(sys.argv)>3 else '1,100,1000,5000'
    if not re.fullmatch(r'\d+(?:,\d+){0,7}',value):raise SystemExit('Expected one to eight comma-separated positive integer sky gains')
    sky_gains=[int(v) for v in value.split(',')]
    if len(set(sky_gains))!=len(sky_gains) or any(not 0<v<=100000 for v in sky_gains):raise SystemExit('Sky gains must be unique and between1 and100000')
    command+=['-EmeraldLightingSweep','-EmeraldSkyGains='+value]
if mode=='motion':command+=['-EmeraldPreviewFrames=48']
if mode=='contacts':command+=['-EmeraldCaptureCharacters','-EmeraldCapturePerspective']
if mode=='events':
    command=[arg for arg in command if not arg.startswith('-EmeraldCaptureDir=')]
    command+=['-EmeraldEventSmoke','-EmeraldEventShotDir='+str(output/'shots'),'-EmeraldEventReport='+str(output/'event-result.json')]
if mode=='gallery':command=[arg.replace('-ResX=1280','-ResX=2560').replace('-ResY=800','-ResY=1600') for arg in command]
started=time.monotonic()
first=None
process=None


def stop_owned():
    if process is None or process.poll() is not None: return
    process.terminate()
    try:
        process.wait(timeout=60)
    except subprocess.TimeoutExpired:
        state=subprocess.check_output(['ps','-o','stat=','-p',str(process.pid)],text=True).strip()
        if 'E' in state or 'Z' in state:
            raise RuntimeError('Owned engine stuck exiting; launches remain paused, owner recovery required')
        process.kill()
        process.wait(timeout=10)

try:
    from engine_launch_budget import admit_engine
    admit_engine('capture:'+mode)
    with (output/'stdout.log').open('w') as stdout:
        process=subprocess.Popen(command,stdout=stdout,stderr=subprocess.STDOUT,start_new_session=True)
        (output/'owned-process.json').write_text(json.dumps({'pid':process.pid,'project':'unreal/Emerald/Emerald.uproject'})+'\n')
        while process.poll() is None:
            shots=[p for p in (output/'shots').glob('*.png') if p.stat().st_size>0]
            elapsed=time.monotonic()-started
            if shots and first is None:
                first=elapsed
                print('EMERALD_CAPTURE first saved rendered image after',round(first,2),'s',flush=True)
            if first is None and elapsed>120:
                guard=os.environ.get('GPU_SLOT',str(Path.home()/'.cache/gpu-slot/bin/gpu_slot.sh'))
                subprocess.run([guard,'pause','Emerald capture failed to produce frame 1 within 120 s'],check=True)
                stop_owned()
                raise RuntimeError('First-frame watchdog: stopped owned capture and paused launches; no retry')
            if elapsed>600:
                stop_owned()
                raise RuntimeError('Capture sweep exceeded 600 s')
            time.sleep(1)
        if process.returncode:
            raise RuntimeError('Owned game exited '+str(process.returncode))
    expected=([m['name']+'.png' for m in json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/littleroot.json').read_text())['maps']] if mode in ('baseline','wander','quality','perspective','camera_edges') else (['asset-credits.png','source-town-sign.png','source-route-guard.png'] if mode=='events' else [f'Sky_{v}.png' for v in sky_gains]))
    if mode=='quality':
        expected=['TownOverhead.png','TownThirdPerson.png']+[name for name in expected if name!='LittlerootTown.png']
    if mode in ('perspective','camera_edges'):expected=['Perspective_'+name for name in expected]
    if mode=='motion':expected=[f'Motion_{i:04d}.png' for i in range(48)]
    if mode in ('lighting','gallery','motion','contacts'):
        log=(output/'engine.log').read_text(errors='replace')
        samples=re.findall(r'EMERALD_LIGHTING_SAMPLE requested=(\d+) actual=(\d+)',log)
        if samples!=[(str(v),str(v)) for v in sky_gains]:raise RuntimeError('Missing actual native skylight readback: '+str(samples))
        if re.findall(r'EMERALD_LIGHTING_ACTORS count=(\d+)',log)!=['1']*len(sky_gains):raise RuntimeError('Unexpected sky actors')
    if mode=='events':
        event=json.loads((output/'event-result.json').read_text(encoding='utf-8-sig'))
        if not event.get('success'):raise RuntimeError('Source event input scenario failed')
    for name in expected:
        if not (output/'shots'/name).is_file(): raise RuntimeError('Missing actual game screenshot '+name)
    from verify_render_log import verify
    log_checks=verify(output/'engine.log')
    camera_fits={}
    if mode in ('baseline','wander','quality','perspective','camera_edges'):
        records=re.findall(r'EMERALD_CAPTURE_FIT map=(\S+) props=(\d+) width=([\d.]+) aspect=([\d.]+)',(output/'engine.log').read_text(errors='replace'))
        camera_fits={name:{'mesh_actors':int(count),'ortho_width_cm':float(width),'aspect':float(aspect)} for name,count,width,aspect in records}
        expected_maps={m['id'] for m in json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/littleroot.json').read_text())['maps']}
        if set(camera_fits)!=expected_maps or any(v['mesh_actors']<=0 or not 0<v['ortho_width_cm']<100000 for v in camera_fits.values()):
            raise RuntimeError('Capture camera did not fit actual generated scene bounds: '+str(camera_fits))
    quality_cameras={}
    if mode=='quality':
        qlog=(output/'engine.log').read_text(errors='replace')
        if not re.search(r'r.TextureStreaming\s*=\s*"?0',qlog):raise RuntimeError('Quality still capture texture residency mode was not read back')
        for name,x,y,z,width in re.findall(r'EMERALD_QUALITY_OVERHEAD map=(\S+) target=([\d.-]+),([\d.-]+),([\d.-]+) width=([\d.]+)',qlog):quality_cameras[name]={'target':[float(x),float(y),float(z)],'ortho_width_cm':float(width)}
        views=re.findall(r'EMERALD_QUALITY_VIEW name=(\S+) projection=(\d+)',qlog)
        if len(quality_cameras)!=6 or len(views)!=7 or dict(views).get('TownThirdPerson')!='0':raise RuntimeError('Missing actual seven-view quality cameras/perspective ground view')
    cadence={}
    if mode in ('baseline','wander','quality','perspective','camera_edges'):
        cap_log=(output/'engine.log').read_text(errors='replace')
        cap_records=re.findall(r'EMERALD_FRAME_CAP requested=(\d+) actual=(\d+)',cap_log)
        if len(cap_records)!=6 or any(a!=b or int(a) not in (30,60) for a,b in cap_records):raise RuntimeError('Native frame-cap readback failed')
        for name,frames,wall,fps,cap in re.findall(r'EMERALD_CAPTURE_CADENCE map=(\S+) frames=(\d+) wall_s=([\d.]+) fps=([\d.]+) cap=(\d+)',cap_log):
            cadence[name]={'frames':int(frames),'wall_s':float(wall),'fps':float(fps),'cap':int(cap)}
        if set(cadence)!=expected_maps or any(v['wall_s']<1 or v['fps']>v['cap']+2 for v in cadence.values()):raise RuntimeError('Actual capture cadence exceeds native cap: '+str(cadence))
    character_scenes={}
    if mode in ('baseline','wander','quality','perspective','camera_edges'):
        log=(output/'engine.log').read_text(errors='replace')
        records=re.findall(r'EMERALD_CHARACTER_SCENE map=(\S+) expected=(\d+) rendered=(\d+) diagnostics=(\d+)',log)
        character_scenes={name:{'expected_models':int(expected),'rendered_models':int(rendered),'visible_diagnostics':int(diagnostics)} for name,expected,rendered,diagnostics in records}
        if set(character_scenes)!=expected_maps or sum(x['expected_models'] for x in character_scenes.values())<=0 or any(x['expected_models']!=x['rendered_models'] for x in character_scenes.values()):
            raise RuntimeError('Source character scene coverage failed: '+str(character_scenes))
        if any(x in log for x in ('EMERALD_CHARACTER_LOAD_FAILED','EMERALD_CHARACTER_REGISTRY_MISSING','EMERALD_SOURCE_MAP_FAILED')):raise RuntimeError('Required character assets unavailable')
        if not re.search(r'EMERALD_CHARACTER_PLAYBACK role=\S+ clip=\S+ time=[\d.]+ component_bone_range_cm=[\d.]+',log):raise RuntimeError('No actual sourced animation pose/time readback')
    if mode in ('baseline','wander','quality','perspective','camera_edges'):
        built=json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/level-build-report.json').read_text())
        planned=built.get('fab_foliage_scatter',{}).get('instances',{})
        if planned:
            instances=re.findall(r'EMERALD_FOLIAGE_RUNTIME actor=(\S+) instances=(\d+) collision=(\d+)',log)
            if len(instances)!=len(planned) or sum(int(n) for _,n,_ in instances)!=sum(planned.values()) or any(c!='0' for _,_,c in instances):raise RuntimeError('Saved native foliage runtime count/collision readback differs from plan')
    if mode=='wander':
        resets=set(re.findall(r'EMERALD_CAPTURE_SOURCE_RESET map=(\S+) gender=\d fixture=post-clock',log))
        if resets!=expected_maps:raise RuntimeError('Capture source fixtures were not isolated per map')
        if not re.search(r'EMERALD_AUTONOMOUS_STEP map=MAP_LITTLEROOT_TOWN id=[23] ',log):raise RuntimeError('No actual town wander step completed')
        if not re.search(r'EMERALD_CHARACTER_PLAYBACK role=\S+ clip=\S+Walk time=[\d.]+ component_bone_range_cm=[\d.]+ samples=\d+',log):raise RuntimeError('No settled actual sourced Walk pose/time readback')
    renderer_settings={}
    preview_playback={}
    if mode=='gallery' and start_map=='/Game/QualityGallery/CharacterGirl':
        for state in ('Idle','Walk','Run'):
            if not re.search(r'EMERALD_CHARACTER_CONFIG role=Preview_'+state+r' bones=\d+ materials=\d+ ready=1 probe=\d+ parts=9',log):raise RuntimeError('Complete modular character preview missing: '+state)
            matches=re.findall(r'EMERALD_CHARACTER_PLAYBACK role=Preview_'+state+r' clip=(\S+) time=([\d.]+) component_bone_range_cm=([\d.]+) samples=(\d+) rate=([\d.]+)',log)
            if not matches:raise RuntimeError('No settled native candidate bone/time playback readback: '+state)
            clip,time_value,distance,samples,rate=matches[-1];preview_playback[state]={'clip':clip,'time':float(time_value),'component_bone_range_cm':float(distance),'samples':int(samples),'rate':float(rate)}
    if mode=='gallery' and start_map=='/Game/QualityGallery/CharacterBoy':
        boy=json.loads((ROOT/'data/native-boy-character-gallery-report.json').read_text())
        if boy.get('parts_per_figure')!=11 or not boy.get('common_skeleton'):raise RuntimeError('Complete boy gallery assembly absent')
        if boy.get('states')!=['Reference']:
            if boy.get('states')!=['Idle','Walk','Run']:raise RuntimeError('Unexpected boy preview states')
            for state in ('Idle','Walk','Run'):
                if not re.search(r'EMERALD_CHARACTER_CONFIG role=Preview_Boy'+state+r' bones=\d+ materials=\d+ ready=1 probe=\d+ parts=11',log):raise RuntimeError('Complete boy preview missing: '+state)
                matches=re.findall(r'EMERALD_CHARACTER_PLAYBACK role=Preview_Boy'+state+r' clip=(\S+) time=([\d.]+) component_bone_range_cm=([\d.]+) samples=(\d+) rate=([\d.]+)',log)
                if not matches:raise RuntimeError('No settled native boy playback: '+state)
                clip,time_value,distance,samples,rate=matches[-1];preview_playback[state]={'clip':clip,'time':float(time_value),'component_bone_range_cm':float(distance),'samples':int(samples),'rate':float(rate)}
    if mode=='gallery' and start_map=='/Game/QualityGallery/AdultMan':
        for state in ('Idle','Walk','Run'):
            if not re.search(r'EMERALD_CHARACTER_CONFIG role=Preview_Adult'+state+r' bones=\d+ materials=22 ready=1 probe=\d+ parts=1',log):raise RuntimeError('Complete adult preview missing: '+state)
            matches=re.findall(r'EMERALD_CHARACTER_PLAYBACK role=Preview_Adult'+state+r' clip=(\S+) time=([\d.]+) component_bone_range_cm=([\d.]+) samples=(\d+) rate=([\d.]+)',log)
            if not matches:raise RuntimeError('No settled native adult bone/time readback: '+state)
            clip,time_value,distance,samples,rate=matches[-1];preview_playback[state]={'clip':clip,'time':float(time_value),'component_bone_range_cm':float(distance),'samples':int(samples),'rate':float(rate)}
    if mode=='gallery' and start_map=='/Game/QualityGallery/Riya':
        candidate=json.loads((ROOT/'data/native-riya-gallery-report.json').read_text())
        if candidate['states']!=['Reference']:
            if candidate['states']!=['Idle','Walk','Run','SitDown']:raise RuntimeError('Riya preview states incomplete')
            for state in candidate['states']:
                if not re.search(r'EMERALD_CHARACTER_CONFIG role=Preview_Riya'+state+r' bones=112 materials=31 ready=1 probe=\d+ parts=1',log):raise RuntimeError('Complete Riya native mesh/rig missing '+state)
                if state=='SitDown':
                    if not re.search(r'EMERALD_CHARACTER_SEATED role=Preview_RiyaSitDown clip=\S+',log):raise RuntimeError('Native Riya seated pose missing')
                    preview_playback[state]={'native_seated_pose_verified':True,'contacts_verified':False};continue
                matches=re.findall(r'EMERALD_CHARACTER_PLAYBACK role=Preview_Riya'+state+r' clip=(\S+) time=([\d.]+) component_bone_range_cm=([\d.]+) samples=(\d+) rate=([\d.]+)',log)
                if not matches:raise RuntimeError('No settled Riya bone/time playback '+state)
                clip,time_value,distance,samples,rate=matches[-1];preview_playback[state]={'clip':clip,'time':float(time_value),'component_bone_range_cm':float(distance),'samples':int(samples),'rate':float(rate)}
    if mode=='contacts':
        views=json.loads((ROOT/'data/native-parent-room-views-report.json').read_text())['views'];view=next(v for v in views if v['map']==start_map);role=view['role']
        if not re.search(r'EMERALD_CHARACTER_CONFIG role='+role+r' bones=112 materials=31 ready=1 probe=\d+ parts=1',log):raise RuntimeError('Detailed source parent missing from contact view')
        if not re.search(r'EMERALD_CHARACTER_OBJECT map='+view['source_map']+r' id=\d+ gfx=\d+ symbol=\S+ tile='+','.join(map(str,view['source_tile'])),log):raise RuntimeError('Source parent tile differs from contact view')
        expected_offset=json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/character-assets.json').read_text())['profiles'][role]['seated_offset_cm']
        matches=re.findall(r'EMERALD_CHARACTER_SEATED role='+role+r' clip=\S+ visual_offset_cm=([\d.-]+),([\d.-]+),([\d.-]+)',log)
        if not matches or any(abs(float(a)-b)>.002 for a,b in zip(matches[-1],expected_offset)):raise RuntimeError('Measured source parent seat offset differs')
        if not re.search(r'EMERALD_ROOM_VIEW map='+view['source_map']+r' perspective=1',log):raise RuntimeError('Contact view is not full room mode')
    if mode in ('gallery','motion') and start_map=='/Game/QualityGallery/Parents':
        candidate=json.loads((ROOT/'data/native-parent-gallery-report.json').read_text())
        if {(r['role'],r['state']) for r in candidate['states']}!={(r,s) for r in ('mom','rival_mom') for s in ('Idle','Walk','SitDown')}:raise RuntimeError('Parent states incomplete')
        for row in candidate['states']:
            role=row['preview_role'];profile=candidate['profiles'][row['role']]
            if not re.search(r'EMERALD_CHARACTER_CONFIG role=Preview_'+role+r' bones=112 materials=31 ready=1 probe=\d+ parts=1',log):raise RuntimeError('Complete parent native assembly missing '+role)
            if row['state']=='SitDown':
                matches=re.findall(r'EMERALD_CHARACTER_SEATED role=Preview_'+role+r' clip=(\S+) visual_offset_cm=([\d.-]+),([\d.-]+),([\d.-]+)',log)
                if not matches:raise RuntimeError('Parent native seated visual offset missing')
                clip,*values=matches[-1];actual=[float(v) for v in values]
                if any(abs(a-b)>.002 for a,b in zip(actual,profile['seated_offset_cm'])):raise RuntimeError('Parent native seat offset differs')
                preview_playback[role]={'clip':clip,'visual_offset_cm':actual,'source_anchor_unchanged':True,'contacts_verified':False}
            else:
                matches=re.findall(r'EMERALD_CHARACTER_PLAYBACK role=Preview_'+role+r' clip=(\S+) time=([\d.]+) component_bone_range_cm=([\d.]+) samples=(\d+) rate=([\d.]+)',log)
                if not matches:raise RuntimeError('Parent native bone/time motion missing '+role)
                clip,t,d,n,rate=matches[-1];preview_playback[role]={'clip':clip,'time':float(t),'component_bone_range_cm':float(d),'samples':int(n),'rate':float(rate)}
    if mode=='gallery' and start_map=='/Game/QualityGallery/Cast':
        candidate=json.loads((ROOT/'data/native-cast-gallery-report.json').read_text())
        if [r['role'] for r in candidate['roles']]!=['birch','fat_man','norman','boy','sibling']:raise RuntimeError('Cast candidate roles incomplete')
        for row in candidate['roles']:
            role=row['role'];p=row['profile'];bones=101 if row['base']=='adult' else 556
            config=r'EMERALD_CHARACTER_CONFIG role=Preview_Cast_'+role+r' bones='+str(bones)+r' materials='+str(len(p['materials']))+r' ready=1 probe=\d+ parts='+str(1+len(p.get('mesh_parts',[])))
            if not re.search(config,log):raise RuntimeError('Cast complete native assembly missing '+role)
            matches=re.findall(r'EMERALD_CHARACTER_PLAYBACK role=Preview_Cast_'+role+r' clip=(\S+) time=([\d.]+) component_bone_range_cm=([\d.]+) samples=(\d+) rate=([\d.]+)',log)
            if not matches:raise RuntimeError('Cast native idle bone/time missing '+role)
            clip,t,d,n,rate=matches[-1];preview_playback[role]={'clip':clip,'time':float(t),'component_bone_range_cm':float(d),'samples':int(n),'rate':float(rate)}
    if mode in ('quality','perspective','camera_edges'):
        registry=json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/character-assets.json').read_text())
        for role in ('mom','rival_mom'):
            profile=registry['profiles'][role]
            if profile.get('model')!='Fab_Riya_'+role:continue
            if not re.search(r'EMERALD_CHARACTER_CONFIG role='+role+r' bones=112 materials=31 ready=1 probe=\d+ parts=1',log):raise RuntimeError('Complete detailed parent missing from source world '+role)
            matches=re.findall(r'EMERALD_CHARACTER_SEATED role='+role+r' clip=(\S+) visual_offset_cm=([\d.-]+),([\d.-]+),([\d.-]+)',log)
            if not matches:raise RuntimeError('Source-world parent seated offset missing '+role)
            _,*values=matches[-1]
            if any(abs(float(a)-b)>.002 for a,b in zip(values,profile['seated_offset_cm'])):raise RuntimeError('Source-world parent seat offset differs '+role)
        if registry['profiles']['player_male'].get('model')=='Fab_CartoonYoungBoy':
            if not re.search(r'EMERALD_CHARACTER_CONFIG role=player_male bones=556 materials=5 ready=1 probe=\d+ parts=11',log):raise RuntimeError('Complete detailed player missing from actual world')
            if not re.search(r'EMERALD_CHARACTER_PLAYBACK role=player_male clip=BoyFK_Casual_MaleIdle time=[\d.]+ component_bone_range_cm=[\d.]+',log):raise RuntimeError('Detailed player native world idle not verified')
        for name in ('r.DynamicGlobalIlluminationMethod','r.ReflectionMethod','r.Lumen.DiffuseIndirect.Allow','r.Lumen.Reflections.Allow'):
            values=re.findall(re.escape(name)+r' = "(\d+)"',log)
            if not values or any(v!='1' for v in values):raise RuntimeError('Required Lumen setting readback differs: '+name)
            renderer_settings[name]=int(values[-1])
    perspective_views={}
    room_presentation={}
    if mode in ('perspective','camera_edges'):
        poses=re.findall(r'EMERALD_PERSPECTIVE_POSE map=(\S+) tile=(\d+),(\d+) collision=(\d+)',log)
        views=re.findall(r'EMERALD_PERSPECTIVE_VIEW map=(\S+) projection=(\d+) fov=([\d.]+) camera=(.*?) rotation=(.*?)\n',log)
        maps={m['id']:m for m in json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/littleroot.json').read_text())['maps']}
        if len(poses)!=6 or len(views)!=6 or {v[0] for v in views}!=set(maps):raise RuntimeError('Missing native six-map perspective camera evidence')
        for name,x,y,collision in poses:
            cells=maps[name]['geometry']['cells'];cell=next((c for c in cells if c['x']==int(x) and c['y']==int(y)),None)
            if not cell or cell['collision'] or collision!='0':raise RuntimeError('Perspective pose is not an actual walkable source tile')
            perspective_views[name]={'tile':[int(x),int(y)],'collision':0}
        for name,projection,fov,camera,rotation in views:
            if projection!='0' or abs(float(fov)-65)>1e-3:raise RuntimeError('Actual perspective camera mode differs')
            perspective_views[name].update(projection='Perspective',fov=float(fov),camera=camera,rotation=rotation)
        lock_path=ROOT/'data/perspective-camera-lock.json'
        if lock_path.exists() and mode=='perspective':
            locked=json.loads(lock_path.read_text())['maps']
            if perspective_views!=locked:raise RuntimeError('Supplemental perspective camera poses differ from inspected baseline')
        built=json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/level-build-report.json').read_text())['maps']
        names={m['id']:m['name'] for m in maps.values()}
        states=re.findall(r'EMERALD_ROOM_VIEW map=(\S+) perspective=(\d+) shown=(\d+) hidden=(\d+) local_lights=(\d+)',log)
        exposures=re.findall(r'EMERALD_ROOM_EXPOSURE map=(\S+) perspective=(\d+) bias=([\d.-]+)',log)
        if len(states)!=6 or len(exposures)!=6:raise RuntimeError('Missing actual room presentation/exposure readbacks')
        for name,perspective,shown,hidden,lights in states:
            planned=built[names[name]].get('perspective_room_shell',{})
            expected_actors=len(planned.get('third_person_only_actors',[]));expected_lights=len(planned.get('local_lights',[]))
            if perspective!='1' or int(shown)!=expected_actors or hidden!='0' or int(lights)!=expected_lights:raise RuntimeError('Room camera visibility/light counts differ from saved content')
            room_presentation[name]={'shown_actors':int(shown),'hidden_actors':int(hidden),'local_lights':int(lights)}
        for name,perspective,bias in exposures:
            expected_bias=0. if name=='MAP_LITTLEROOT_TOWN' else 3.
            if perspective!='1' or abs(float(bias)-expected_bias)>1e-4:raise RuntimeError('Native room exposure differs')
            room_presentation[name]['exposure_bias']=float(bias)
        if mode=='camera_edges':
            checks=re.findall(r'EMERALD_CAMERA_BOUNDARY map=(\S+) inside=(\d+)',log)
            if len(checks)!=6 or {n for n,_ in checks}!=set(maps) or any(v!='1' for _,v in checks):raise RuntimeError('Actual room-boundary camera checks failed')

    motion_frames=[]
    if mode=='motion':
        motion_frames=[{'index':int(i),'time_s':float(t)} for i,t in re.findall(r'EMERALD_PREVIEW_FRAME index=(\d+) time_s=([\d.]+)',log)]
        if [f['index'] for f in motion_frames]!=list(range(48)) or not re.search(r'EMERALD_PREVIEW_COMPLETE frames=48',log):raise RuntimeError('Native motion sequence incomplete')
        if any(b['time_s']<=a['time_s'] for a,b in zip(motion_frames,motion_frames[1:])):raise RuntimeError('Native motion time did not advance')
        durations=[b['time_s']-a['time_s'] for a,b in zip(motion_frames,motion_frames[1:])];last=sorted(durations)[len(durations)//2]
        lines=['ffconcat version 1.0']
        for i,duration in enumerate(durations+[last]):lines.extend(["file 'shots/Motion_%04d.png'"%i,'duration %.6f'%duration])
        lines.append("file 'shots/Motion_0047.png'");(output/'motion.ffconcat').write_text('\n'.join(lines)+'\n')
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','1','-i',str(output/'motion.ffconcat'),'-fps_mode','vfr','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-movflags','+faststart','-map_metadata','-1',str(output/'native-motion.mp4')],check=True)
    (output/'result.json').write_text(json.dumps({'success':True,'scenario':mode,'first_saved_frame_s':first,'screenshots':expected,'inspection_complete':False,'render_log_checks':log_checks,'camera_fits':camera_fits,'character_scenes':character_scenes,'cadence':cadence,'quality_cameras':quality_cameras,'renderer_settings':renderer_settings,'preview_playback':preview_playback,'perspective_views':perspective_views,'room_presentation':room_presentation,'motion_frames':motion_frames},indent=2)+'\n')
    print('Saved scenario game screenshots; visual inspection still required:',mode)
finally:
    stop_owned()
