#!/usr/bin/env python3
"""Restore only hash-pinned, browser-acquired Fab ground maps."""
import json,hashlib,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];lock=json.loads((ROOT/'data/fab-lawn-lock.json').read_text());archive=ROOT/lock['archive'];source=archive if archive.exists() else Path.home()/'Downloads'/archive.name
raw=source.read_bytes()
if len(raw)!=lock['archive_bytes'] or hashlib.sha256(raw).hexdigest()!=lock['archive_sha256']:raise SystemExit('Licensed lawn archive differs; preserved')
archive.parent.mkdir(parents=True,exist_ok=True)
if not archive.exists():shutil.copyfile(source,archive)
with zipfile.ZipFile(archive) as z:
    if set(z.namelist())!={f['member'] for f in lock['files']}:raise SystemExit('Unexpected lawn archive members')
    for f in lock['files']:
        p=(ROOT/f['path']).resolve()
        if not p.is_relative_to((ROOT/'assets/source/quality-lawn').resolve()) or f['bytes']>64*1024*1024:raise SystemExit('Unsafe lawn dependency')
        raw=z.read(f['member'])
        if len(raw)!=f['bytes'] or hashlib.sha256(raw).hexdigest()!=f['sha256']:raise SystemExit('Lawn source differs')
        if p.exists() and p.read_bytes()!=raw:raise SystemExit('Existing lawn source differs; preserved')
        p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():p.write_bytes(raw)
print('Verified complete original4K scanned lawn maps')
