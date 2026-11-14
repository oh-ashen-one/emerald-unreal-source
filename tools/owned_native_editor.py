#!/usr/bin/env python3
"""Exec the task-owned native editor beneath gpu_slot and record its identity."""
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
if not os.environ.get('GPU_SLOT_HELD'):raise SystemExit('Shared GPU guard required')
receipt=ROOT/'out/native-editor/owned-process.json'
if receipt.exists():
    old=json.loads(receipt.read_text())
    try:os.kill(old['pid'],0)
    except ProcessLookupError:pass
    else:raise SystemExit('Previous owned editor receipt still has a live PID; inspect before relaunch')
port=int(os.environ.get('EMERALD_MCP_PORT','8876'))
listeners=subprocess.run(['lsof','-nP',f'-iTCP:{port}','-sTCP:LISTEN','-t'],capture_output=True,text=True)
if listeners.stdout.strip():raise SystemExit('Native editor port is already held; preserving its owner')
pid=os.getpid();project=ROOT/'unreal/Emerald/Emerald.uproject'
receipt.parent.mkdir(parents=True,exist_ok=True)
receipt.write_text(json.dumps({'pid':pid,'start_identity':subprocess.check_output(['ps','-p',str(pid),'-o','lstart='],text=True).strip(),'project':str(project),'port':port},indent=2)+'\n')
engine=Path(os.environ.get('UE_ROOT','/Users/Shared/Epic Games/UE_5.8'))/'Engine/Binaries/Mac/UnrealEditor-Cmd'
rhi=os.environ.get('EMERALD_EDITOR_RHI','null')
if rhi not in ('null','offscreen'):raise SystemExit('Expected null or offscreen owned editor mode')
args=[str(engine),str(project),'-nullrhi' if rhi=='null' else '-RenderOffScreen','-unattended','-nosound','-nosplash','-NoCrashReports',
      '-ModelContextProtocolStartServer','-ModelContextProtocolPort='+str(port),
      '-dpcvars=t.MaxFPS='+os.environ.get('GPU_SLOT_FPS_CAP','60'),'-abslog='+str(ROOT/'out/native-editor/engine.log')]
os.execv(str(engine),args)
