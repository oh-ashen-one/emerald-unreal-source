#!/usr/bin/env python3
"""Verify a licensed browser download and extract only the pinned GLB member."""
import hashlib,json,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def acquire():
    for item in json.loads((ROOT/'data/fab-character-quality-lock.json').read_text())['assets']:
        archive=ROOT/item['archive'];source=archive if archive.exists() else Path.home()/'Downloads'/archive.name;target=ROOT/item['file']
        if not archive.resolve().is_relative_to((ROOT/'assets/source/fab-characters').resolve()) or not target.resolve().is_relative_to((ROOT/'assets/source/fab-characters').resolve()):raise SystemExit('Unsafe character source path')
        raw=source.read_bytes()
        if len(raw)!=item['archive_bytes'] or hashlib.sha256(raw).hexdigest()!=item['archive_sha256']:raise SystemExit('Licensed archive differs; preserved')
        archive.parent.mkdir(parents=True,exist_ok=True)
        if not archive.exists():shutil.copyfile(source,archive)
        with zipfile.ZipFile(archive) as bundle:
            files=bundle.infolist()
            if len(files)!=1 or files[0].filename!=item['archive_member'] or files[0].file_size!=item['bytes']:raise SystemExit('Unexpected archive members; nothing extracted')
            data=bundle.read(files[0])
        if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:raise SystemExit('Source character bytes differ')
        if target.exists() and target.read_bytes()!=data:raise SystemExit('Existing character differs; preserved')
        if not target.exists():target.write_bytes(data)
    print('Verified licensed free Fab character archive and complete original GLB; no scripts executed')
if __name__=='__main__':acquire()
