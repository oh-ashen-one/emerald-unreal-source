#!/usr/bin/env python3
"""Exec the owned authoring commandlet with real-RHI compilation and guard cap."""
import os
import sys
from pathlib import Path
if not os.environ.get('GPU_SLOT_HELD'):raise SystemExit('Shared GPU guard required')
root=Path(__file__).resolve().parents[1];engine=Path(os.environ.get('UE_ROOT','/Users/Shared/Epic Games/UE_5.8'))
script=sys.argv[1] if len(sys.argv)>1 else 'build_levels.py'
folders={'build_levels.py':'level-build','build_village_gallery.py':'village-gallery-build','import_quality_character.py':'quality-character-import','build_character_gallery.py':'quality-character-gallery-build','retarget_quality_character.py':'quality-character-retarget','build_character_profiles.py':'character-profile-build','import_adult_character.py':'quality-adult-import','build_adult_gallery.py':'quality-adult-gallery-build','adapt_adult_materials.py':'quality-adult-materials','retarget_adult_character.py':'quality-adult-retarget'}
folders.update({'import_boy_character.py':'quality-boy-import','build_boy_gallery.py':'quality-boy-gallery-build','retarget_boy_character.py':'quality-boy-retarget','adapt_boy_materials.py':'quality-boy-materials'})
folders['build_fixture_gallery.py']='quality-fixture-gallery-build'
folders['inspect_riya_character.py']='quality-riya-inspection'
folders['build_riya_gallery.py']='quality-riya-gallery-build'
folders['repair_riya_dependencies.py']='quality-riya-dependency-repair'
folders['retarget_riya_character.py']='quality-riya-retarget'
folders['build_cast_gallery.py']='quality-cast-gallery-build'
folders['build_parent_gallery.py']='quality-parent-gallery-build'
folders['inspect_riya_supplied_motion.py']='quality-riya-supplied-motion-inspection'
folders['build_parent_room_views.py']='quality-parent-room-view-build'
folders['inspect_parent_contacts.py']='quality-parent-contact-pose-inspection'
folders['correct_parent_seat_contact.py']='quality-parent-seat-contact-correction'
folders['build_parent_contact_pass.py']='quality-parent-contact-pass-build'
if script not in folders:raise SystemExit('Unknown owned authoring script')
log=root/'out'/folders[script]/'engine.log';log.parent.mkdir(parents=True,exist_ok=True)
profile='t.MaxFPS='+os.environ.get('GPU_SLOT_FPS_CAP','60')+(',Interchange.FeatureFlags.Import.FBX=0' if script=='import_adult_character.py' else '')
execution=['-ExecutePythonScript='+str(root/'tools'/script)] if script=='import_adult_character.py' else ['-run=pythonscript','-script='+str(root/'tools'/script),'-AllowCommandletRendering']
if script in ('inspect_parent_contacts.py','correct_parent_seat_contact.py'):execution=[a for a in execution if a!='-AllowCommandletRendering']+['-nullrhi']
# Legacy FBX's warning logger needs a real Slate application. The installed
# editor startup-script runner initializes Slate, runs unattended, then quits.
command=[str(engine/'Engine/Binaries/Mac/UnrealEditor-Cmd'),str(root/'unreal/Emerald/Emerald.uproject'),*execution,'-RenderOffScreen','-unattended','-nosound','-nosplash','-NoCrashReports','-dpcvars='+profile,'-abslog='+str(log)]
from engine_launch_budget import admit_engine
admit_engine('authoring:'+script)
os.execv(command[0],command)
