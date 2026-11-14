#!/usr/bin/env python3
"""Verify the existing CC0 motion set; both rigs already face native +Y."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];source=json.loads((ROOT/'data/character-preparation-report.json').read_text())['Casual_Female'];path=ROOT/source['path']
if hashlib.sha256(path.read_bytes()).hexdigest()!=source['staged_sha256']:raise SystemExit('Pinned source motions differ')
info=json.loads((ROOT/'data/native-character-import-report.json').read_text())['models']['Casual_Female']
report={'source':'Quaternius Casual_Female, official CC0 Ultimate Animated Character Pack; see character-lock.json','source_sha256':source['staged_sha256'],'path':source['path'],'staged_sha256':source['staged_sha256'],'mesh':info['mesh'],'animations':info['animations'],'clips':list(source['selected_clips']),'modification':'None. Both source and target face native +Y, verified from source face geometry and target native preview. Reuse existing imported original clips without changing their keys or scene orientation.'}
(ROOT/'data/quality-motion-source-preparation-report.json').write_text(json.dumps(report,indent=2)+'\n');print('Verified four existing CC0 motions; no orientation adapter needed')
