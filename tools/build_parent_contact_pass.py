"""Batch related native authoring in one owned engine admission."""
import runpy
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1]
for script in ('correct_parent_seat_contact.py','build_riya_gallery.py','build_parent_gallery.py'):
    runpy.run_path(str(ROOT/'tools'/script),run_name='__main__')
print('Saved sourced parent contact derivative and candidate studios in one engine run')
