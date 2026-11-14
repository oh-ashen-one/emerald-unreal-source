"""Read-only native audit of selected licensed quality assets."""
import json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1]
if Path(unreal.Paths.get_project_file_path()).resolve()!=ROOT/'unreal/Emerald/Emerald.uproject':raise RuntimeError('Unexpected project')
lock=json.loads((ROOT/'data/epic-quality-lock.json').read_text())
mesh=unreal.load_asset(lock['package'])
if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError('Installed tree mesh unavailable')
b=mesh.get_bounds();materials=[]
for slot in mesh.get_editor_property('static_materials'):
    mat=slot.material_interface
    if mat is None:raise RuntimeError('Missing tree material')
    graph={};textures=set()
    for key,prop in [('color',unreal.MaterialProperty.MP_BASE_COLOR),('normal',unreal.MaterialProperty.MP_NORMAL),('roughness',unreal.MaterialProperty.MP_ROUGHNESS),('specular',unreal.MaterialProperty.MP_SPECULAR),('opacity',unreal.MaterialProperty.MP_OPACITY_MASK)]:
        pending=[unreal.MaterialEditingLibrary.get_material_property_input_node(mat,prop)];seen=set();nodes=[]
        while pending:
            node=pending.pop()
            if node is None or node.get_path_name() in seen:continue
            seen.add(node.get_path_name());nodes.append(node.get_class().get_name())
            if isinstance(node,unreal.MaterialExpressionTextureSample):
                texture=node.get_editor_property('texture')
                if texture is None:raise RuntimeError('Unbound original tree texture')
                textures.add(texture.get_path_name())
            pending.extend(unreal.MaterialEditingLibrary.get_inputs_for_material_expression(mat,node))
        graph[key]=nodes
    if not textures or 'MaterialExpressionTextureSample' not in graph['normal']:raise RuntimeError('Required source tree texture/normal bindings absent')
    materials.append({'slot':str(slot.material_slot_name),'material':mat.get_path_name(),'textures':sorted(textures),'property_graphs':graph})
report={'package':mesh.get_path_name(),'bounds_origin':[b.origin.x,b.origin.y,b.origin.z],'bounds_extent':[b.box_extent.x,b.box_extent.y,b.box_extent.z],'lods':mesh.get_num_lods(),'triangles_per_lod':[mesh.get_num_triangles(i) for i in range(mesh.get_num_lods())],'materials':materials,'runtime_render_inspected':False}
p=ROOT/'data/native-quality-asset-audit.json';p.write_text(json.dumps(report,indent=2)+'\n');print('Native quality asset audit:',json.dumps(report))
