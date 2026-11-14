#!/usr/bin/env python3
"""Task-local hourly admission guard, in addition to the shared GPU FIFO."""
import argparse,datetime,fcntl,json,os,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LIMIT=10
class LaunchBudgetExceeded(RuntimeError):pass

def update(root=ROOT, *, admit=None, now=None):
    now=now or datetime.datetime.now(datetime.timezone.utc)
    ledger=root/'out/engine-launch-budget.json';ledger.parent.mkdir(parents=True,exist_ok=True)
    with os.fdopen(os.open(ledger,os.O_RDWR|os.O_CREAT,0o600),'r+') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX)
        raw=stream.read()
        if raw:
            data=json.loads(raw)
            if data.get('schema')!='emerald.engine-launch-budget/1':raise RuntimeError('Unexpected task launch ledger; preserved')
        else:
            # Seed once from prior task-owned receipts. After this checkpoint,
            # every automated native entrypoint records an admission here.
            rows={}
            for path in (root/'out').rglob('*gpu*.json'):
                try:x=json.loads(path.read_text())
                except (OSError,json.JSONDecodeError):continue
                if not isinstance(x,dict) or x.get('cwd')!=str(root) or not str(x.get('label','')).startswith('emerald-') or not x.get('started_at'):continue
                time=datetime.datetime.fromisoformat(x['started_at'])
                if (now-time).total_seconds()<3600:rows[(x['started_at'],x.get('pid'))]={'time':time.isoformat(),'label':x['label'],'origin':'prior shared-slot receipt'}
            data={'schema':'emerald.engine-launch-budget/1','seeded_at':now.isoformat(),'entries':list(rows.values()),'scope':'Automated task engine admissions, including null-RHI; supplements shared FIFO, no global safeguard change'}
        # A backwards wall-clock adjustment must not erase recent admissions.
        entries=[r for r in data['entries'] if (now-datetime.datetime.fromisoformat(r['time'])).total_seconds()<3600]
        entries.sort(key=lambda r:datetime.datetime.fromisoformat(r['time']))
        available=now if len(entries)<LIMIT else datetime.datetime.fromisoformat(entries[len(entries)-LIMIT]['time'])+datetime.timedelta(hours=1,milliseconds=1)
        status={'count_last_hour':len(entries),'limit':LIMIT,'can_launch':len(entries)<LIMIT,'next_available_utc':available.astimezone(datetime.timezone.utc).isoformat()}
        if admit and status['can_launch']:entries.append({'time':now.isoformat(),'label':admit,'origin':'task admission'})
        data['entries']=entries;stream.seek(0);json.dump(data,stream,indent=2);stream.write('\n');stream.truncate();stream.flush();os.fsync(stream.fileno())
        if admit and not status['can_launch']:raise LaunchBudgetExceeded('Task engine limit: '+str(status['count_last_hour'])+'/10 starts in last hour; next admission '+status['next_available_utc'])
        return status

def admit_engine(label):
    if not os.environ.get('GPU_SLOT_HELD'):raise RuntimeError('Shared GPU FIFO still required')
    return update(admit=label)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--label',default='native-test');parser.add_argument('--exec',dest='command',nargs=argparse.REMAINDER);args=parser.parse_args()
    if args.check:
        status=update();print(json.dumps(status));sys.exit(0 if status['can_launch'] else 81)
    if not args.command or len(args.command)<2:parser.error('Use --check or --exec with native editor/project arguments')
    engine=Path(os.environ.get('UE_ROOT','/Users/Shared/Epic Games/UE_5.8'))/'Engine/Binaries/Mac/UnrealEditor-Cmd'
    if Path(args.command[0]).resolve()!=engine.resolve() or Path(args.command[1]).resolve()!=ROOT/'unreal/Emerald/Emerald.uproject':raise SystemExit('Unexpected task engine/project')
    try:admit_engine(args.label)
    except LaunchBudgetExceeded as error:raise SystemExit(str(error))
    if not any(a.startswith('-dpcvars=') and 't.MaxFPS=' in a for a in args.command):
        args.command.append('-dpcvars=t.MaxFPS='+os.environ.get('GPU_SLOT_FPS_CAP','60'))
    os.execv(str(engine),args.command)
