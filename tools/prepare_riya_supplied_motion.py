#!/usr/bin/env python3
"""Select three supplied native animation sequences; never stage controllers."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];lock=json.loads((ROOT/'data/fab-riya-character-lock.json').read_text());archive=ROOT/lock['archive']
if hashlib.sha256(archive.read_bytes()).hexdigest()!=lock['archive_sha256']:raise SystemExit('Original Fab archive hash differs')
rows=[]
with zipfile.ZipFile(archive) as package:
    for name in ('MF_Idle','MF_Walk_Fwd','MF_Run_Fwd'):
        member='Realisticgirl/Animation/'+name+'.uasset';data=package.read(member);target=ROOT/'unreal/Emerald/Content'/member
        if len(data)>4*1024*1024:raise SystemExit('Unexpected supplied animation size')
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and target.read_bytes()!=data:raise SystemExit('Existing supplied animation differs; preserved')
        if not target.exists():target.write_bytes(data)
        rows.append({'member':member,'path':str(target.relative_to(ROOT)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
(ROOT/'data/riya-supplied-motion-source-report.json').write_text(json.dumps({'source':lock['url'],'license':lock['license'],'files':rows,'selection':'Only three native AnimSequence candidates supplied in the original licensed archive. ABPs, BlendSpaces and demo maps remain excluded. No supplied controller executed. Initial character intake excluded these clips; this supplemental selection supersedes that exclusion for these three files only.','quality_gate_passed':False},indent=2)+'\n')
print('Staged three original supplied motion candidates, source bytes preserved')
