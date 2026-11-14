#!/usr/bin/env python3
"""Stage licensed native character data without source demos/Blueprint execution."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
lock_path=ROOT/'data/fab-riya-character-lock.json';lock=json.loads(lock_path.read_text());archive=ROOT/lock['archive'];raw=archive.read_bytes()
if len(raw)!=lock['archive_bytes'] or hashlib.sha256(raw).hexdigest()!=lock['archive_sha256']:raise SystemExit('Licensed Riya archive differs; preserved')
content=ROOT/'unreal/Emerald/Content';rows=[];excluded=[]
with zipfile.ZipFile(archive) as package:
    if sum(i.file_size for i in package.infolist())>512*1024*1024:raise SystemExit('Unexpected expanded native character size')
    for member in package.infolist():
        name=member.filename
        if member.is_dir():continue
        target=(content/name).resolve()
        if not target.is_relative_to((content/'Realisticgirl').resolve()) or member.file_size>64*1024*1024 or (member.external_attr>>16)&0o170000==0o120000:raise SystemExit('Unexpected native character archive member')
        if '/DemoMap/' in name or '/Animation/' in name or not name.endswith(('.uasset','.uexp','.ubulk')):excluded.append(name);continue
        data=package.read(member);target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and target.read_bytes()!=data:raise SystemExit('Existing native source differs; preserved '+name)
        if not target.exists():target.write_bytes(data)
        rows.append({'member':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'path':str(target.relative_to(ROOT))})
report={'source':lock['url'],'license':lock['license'],'native_files':rows,'excluded':excluded,'scope':'Native data staged with exact source bytes; demo maps/animation controllers/clips excluded from runtime selection. Rig/material/complete mesh and source-motion fit require native inspection.','quality_gate_passed':False}
(ROOT/'data/riya-native-source-report.json').write_text(json.dumps(report,indent=2)+'\n');print('Staged native Riya dependencies',len(rows),'files; excluded demos/animation assets',len(excluded))
