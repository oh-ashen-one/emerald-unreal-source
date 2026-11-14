#!/usr/bin/env python3
"""Verify original CC-BY files and stage portable FBX texture lookup copies."""
import json,hashlib,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];lock=json.loads((ROOT/'data/fab-adult-character-lock.json').read_text());dest=ROOT/'unreal/Emerald/Content/Imported/QualityAdultSources';dest.mkdir(parents=True,exist_ok=True)
archive=ROOT/lock['archive'];download=archive if archive.exists() else Path.home()/'Downloads'/archive.name
raw_archive=download.read_bytes()
if len(raw_archive)!=lock['archive_bytes'] or hashlib.sha256(raw_archive).hexdigest()!=lock['archive_sha256']:raise SystemExit('Licensed adult archive differs')
archive.parent.mkdir(parents=True,exist_ok=True)
if not archive.exists():shutil.copyfile(download,archive)
expected={item['member']:item for item in lock['files']}
with zipfile.ZipFile(archive) as bundle:
    if set(bundle.namelist())!=set(expected):raise SystemExit('Unexpected adult archive members')
    for info in bundle.infolist():
        item=expected[info.filename];target=(ROOT/item['path']).resolve()
        if not target.is_relative_to((ROOT/'assets/source/fab-characters/CaninoGameMan').resolve()) or info.file_size!=item['bytes'] or info.file_size>64*1024*1024:raise SystemExit('Unsafe adult archive member')
        data=bundle.read(info)
        if hashlib.sha256(data).hexdigest()!=item['sha256']:raise SystemExit('Adult member bytes differ')
        if target.exists() and target.read_bytes()!=data:raise SystemExit('Existing adult source differs; preserved')
        if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
for item in lock['files']:
    source=ROOT/item['path'];raw=source.read_bytes()
    if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:raise SystemExit('Original adult source differs; preserved')
    target=dest/source.name
    if target.exists() and target.read_bytes()!=raw:raise SystemExit('Existing adult derivative differs; preserved')
    if not target.exists():shutil.copyfile(source,target)
print('Verified40 original adult FBX/texture inputs; portable lookup copies only')
