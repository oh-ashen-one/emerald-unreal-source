"""Create source-role character materials and runtime descriptors in owned content."""
import json,sys
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1]
if Path(unreal.Paths.get_project_file_path()).resolve()!=ROOT/'unreal/Emerald/Emerald.uproject':raise RuntimeError('Unexpected project')
sys.path.insert(0,str(ROOT/'tools'))
from material_graph import clear_material
EAL=unreal.EditorAssetLibrary;TOOLS=unreal.AssetToolsHelpers.get_asset_tools();LIB=unreal.MaterialEditingLibrary
imports=json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/character-import-report.json').read_text());plan=json.loads((ROOT/'data/character-role-plan.json').read_text());prep=json.loads((ROOT/'data/character-preparation-report.json').read_text())
folder='/Game/Imported/CharacterMaterials';EAL.make_directory(folder);path=folder+'/CharacterPalette'
parent=unreal.load_asset(path) if EAL.does_asset_exist(path) else TOOLS.create_asset('CharacterPalette',folder,unreal.Material,unreal.MaterialFactoryNew())
clear_material(parent,unreal)
color=LIB.create_material_expression(parent,unreal.MaterialExpressionVectorParameter,-200,0);color.set_editor_property('parameter_name','Color');color.set_editor_property('default_value',unreal.LinearColor(1,1,1,1))
rough=LIB.create_material_expression(parent,unreal.MaterialExpressionConstant,-200,140);rough.set_editor_property('r',.8)
for node,out,prop in [(color,'',unreal.MaterialProperty.MP_BASE_COLOR),(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)]:
 if not LIB.connect_material_property(node,out,prop):raise RuntimeError('Character palette graph disconnected')
LIB.set_material_usage(parent,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH);LIB.recompile_material(parent)
error=unreal.EmeraldAuthoringLibrary.compile_material(parent)
if error:raise RuntimeError('Native character palette compilation failed: '+error)
EAL.save_loaded_asset(parent)
if 'Color' not in [str(n) for n in LIB.get_vector_parameter_names(parent)]:raise RuntimeError('Character palette parameter not exposed')
def linear(c):
 c=c/255.;return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
profiles={}
for key,profile in plan['profiles'].items():
 info=imports[profile['model']];original=prep[profile['model']]['materials'];materials=[]
 for slot in info['material_slots']:
  matches=[name for name in original if slot==name or slot.endswith('_'+name)]
  if len(matches)!=1:raise RuntimeError('Inspect unrecognized native material slot '+slot)
  semantic=matches[0];rgb=profile['colors_rgb8'].get(semantic,profile['colors_rgb8'].get({'Shirt':'Main','Pants':'Black','Belt':'Brown'}.get(semantic,'')));rgba=[linear(c) for c in rgb]+[1] if rgb else original[semantic]
  name=key+'_'+semantic;path=folder+'/'+name;mi=unreal.load_asset(path) if EAL.does_asset_exist(path) else TOOLS.create_asset(name,folder,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
  LIB.set_material_instance_parent(mi,parent)
  # Installed UE5.8 implementation sets/updates but unconditionally returns false.
  LIB.set_material_instance_vector_parameter_value(mi,'Color',unreal.LinearColor(*rgba))
  actual=LIB.get_material_instance_vector_parameter_value(mi,'Color')
  if any(abs(a-b)>1e-5 for a,b in zip((actual.r,actual.g,actual.b,actual.a),rgba)):raise RuntimeError('Character color readback differs')
  EAL.save_loaded_asset(mi);materials.append(mi.get_path_name())
 clips={action:info['animations'][source]['asset'] for action,source in info['animation_aliases'].items()}
 profiles[key]={**profile,'mesh':info['mesh'],'animations':clips,'materials':materials,'source_joint_count':info['source_joint_count']}
# Original event identity is data-only; presentation uses a licensed generic
# supply case rather than the source game's distinctive colored-ball design.
fixtures=json.loads((ROOT/'data/native-quality-fixture-report.json').read_text())
case_source=fixtures['cardboard_box_01'];case=unreal.load_asset(case_source['mesh'])
if not isinstance(case,unreal.StaticMesh) or case.get_num_triangles(0)!=case_source['triangles']:raise RuntimeError('Complete scanned supply box missing or reduced')
case_materials=[slot.get_editor_property('material_interface').get_path_name() for slot in case.get_editor_property('static_materials')]
if not case_materials:raise RuntimeError('Licensed supply-case materials missing')
profiles['item_ball']={'kind':'static','static_mesh':case.get_path_name(),'diameter_cm':110,'materials':case_materials,'source_graphics':'OBJ_EVENT_GFX_ITEM_BALL','appearance':'Complete scanned generic cardboard supply box; original event/position/visibility and pickup semantics retained','license':'CC0-1.0','source':case_source['source']}
(ROOT/'data/native-pickup-profile-report.json').write_text(json.dumps({'mesh':case.get_path_name(),'triangles':case.get_num_triangles(0),'materials':case_materials,'diameter_cm':110,'source':case_source['source'],'license':'CC0-1.0','source_graphics':'OBJ_EVENT_GFX_ITEM_BALL','scope':'Native complete scanned static mesh/material descriptor verified; runtime floor/scale/visibility and appearance require inspection','inspection_complete':False},indent=2)+'\n')
constants=json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/source-events.json').read_text())['constants'];plan['graphics'][str(constants['OBJ_EVENT_GFX_ITEM_BALL'])]='item_ball'
result={**plan,'profiles':profiles}
(ROOT/'unreal/Emerald/Content/Imported/Data/character-assets.json').write_text(json.dumps(result,indent=2)+'\n')
legacy=folder+'/SourceItemBall'
if EAL.does_asset_exist(legacy):
    if EAL.find_package_referencers_for_asset(legacy,load_assets_to_confirm=True):raise RuntimeError('Legacy source-styled pickup still referenced; preserve and inspect')
    if not EAL.delete_asset(legacy):raise RuntimeError('Cannot remove unused source-styled pickup material')
(ROOT/'data/native-character-import-report.json').write_text(json.dumps({'models':imports,'profiles':list(profiles),'scope':'Native assembly/clip/skeleton/material readback; actual playback still required'},indent=2)+'\n')
unreal.log('EMERALD_CHARACTER_PROFILES complete '+str(len(profiles)))
