#!/usr/bin/env python3
"""Verify browser-acquired FREE Fab files; no cookies, auth stores or signed URLs."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--downloads-root',type=Path,default=Path.home()/'Downloads');args=p.parse_args()
for item in json.loads((ROOT/'data/fab-download-lock.json').read_text())['assets']:
    target=ROOT/item['source_file'];source=target if target.exists() else args.downloads_root/target.name
    if source.stat().st_size!=item['bytes'] or hashlib.sha256(source.read_bytes()).hexdigest()!=item['sha256']:raise SystemExit('Selected licensed Fab file differs from lock; preserved')
    if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
print('Verified pinned free Fab source downloads; original bytes unchanged')
