"""Read-only inspection of imported assemblies and the actual floor graph."""
import json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1]
CONTENT=Path(unreal.Paths.project_content_dir())
source=json.loads((CONTENT/'Imported/Data/level-build-report.json').read_text())
report={'meshes':{},'floor_graph':{}}
for name in ['bedSingle','computerScreen','roofGable','tableCrossCloth']:
    entry=source['art'][name];mesh=unreal.load_asset(entry['asset']);b=mesh.get_bounds()
    report['meshes'][name]={'selected_asset':entry['asset'],'selected_bounds_cm':[b.box_extent.x*2,b.box_extent.y*2,b.box_extent.z*2],
        'all_static_mesh_assets':[p for p in unreal.EditorAssetLibrary.list_assets('/Game/Imported/Art/'+name,recursive=True) if isinstance(unreal.load_asset(p),unreal.StaticMesh)]}
mat=unreal.load_asset('/Game/Imported/Materials/WoodFloor_PBR');lib=unreal.MaterialEditingLibrary
for field,prop in [('base_color',unreal.MaterialProperty.MP_BASE_COLOR),('normal',unreal.MaterialProperty.MP_NORMAL),('roughness',unreal.MaterialProperty.MP_ROUGHNESS),('metallic',unreal.MaterialProperty.MP_METALLIC)]:
    node=lib.get_material_property_input_node(mat,prop)
    report['floor_graph'][field]={'expression':node.get_name() if node else None,'output':lib.get_material_property_input_node_output_name(mat,prop)}
report['floor_graph']['expressions']=[]
for node in lib.get_material_expressions(mat):
    item={'name':node.get_name(),'type':node.get_class().get_name(),'input_names':list(lib.get_material_expression_input_names(node)),
          'input_connections':[n.get_name() if n else None for n in lib.get_inputs_for_material_expression(mat,node)]}
    if isinstance(node,(unreal.MaterialExpressionTextureSampleParameter2D,unreal.MaterialExpressionTextureObjectParameter)):
        texture=node.get_editor_property('texture');item['texture']=texture.get_path_name() if texture else None
        if texture:
            item['source_file']=Path(texture.get_editor_property('asset_import_data').get_first_filename()).name
    report['floor_graph']['expressions'].append(item)
(CONTENT/'Imported/Data/native-asset-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
unreal.log('EMERALD_ASSET_INSPECTION '+json.dumps(report))
