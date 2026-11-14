#!/usr/bin/env python3
"""Owner launcher for the saved local standalone; never builds or opens editor."""
import os,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
archive=Path((ROOT/'out/standalone/latest.txt').read_text().strip());apps=list(archive.glob('Mac/*.app'))
if len(apps)!=1:raise SystemExit('Standalone archive is not ready; see PLAY.md')
app=apps[0];executables=[p for p in (app/'Contents/MacOS').iterdir() if p.is_file() and os.access(p,os.X_OK)]
if len(executables)!=1:raise SystemExit('Standalone executable not found')
if not os.environ.get('GPU_SLOT_HELD'):
    guard=Path.home()/'.cache/gpu-slot/bin/gpu_slot.sh'
    command=[str(guard),'capture','--label','emerald-owner-standalone','--timeout','7200','--',sys.executable,str(Path(__file__).resolve()),*sys.argv[1:]]
    os.execv(str(guard),command)
from engine_launch_budget import admit_engine
admit_engine('owner-standalone-play')
fps=os.environ.get('GPU_SLOT_FPS_CAP','30');command=[str(executables[0]),'-windowed','-ResX=1600','-ResY=1000','-EmeraldThirdPerson','-corelimit=16','-dpcvars=t.MaxFPS='+fps,'-NoCrashReports',*sys.argv[1:]]
os.chdir(app.parent);os.execv(command[0],command)
