"""Read native free Fab foliage bounds, LODs, material inheritance and textures."""
import json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1];lib=unreal.MaterialEditingLibrary
base='/Game/StyleHex_Studio/Free_Packs/FREE_Stylized_Forest_Sample'
paths=[*(base+'/Meshes/Trees/SM_Tree_'+name for name in ('Broadleaf_1','Broadleaf_2','Birch_1','Birch_2')),
       *(base+'/Meshes/Foliage/SM_Fol_Grass_Clump_'+str(i) for i in range(1,6)),
       *(base+'/Meshes/Foliage/SM_Fol_Flower_Clump_'+str(i) for i in range(1,4)),
       *(base+'/Meshes/Foliage/SM_Fol_Bush_'+str(i) for i in range(1,3)),
       *(base+'/Meshes/Stones/SM_Stone_'+str(i) for i in range(1,4)),base+'/Meshes/Stones/SM_Stone_Boulder_1']
result={'source':'https://www.fab.com/listings/3c1a31b6-e523-4a0f-97d0-26b0db69b6bc','license':'Fab Standard License','meshes':{},'materials':{},'runtime_inspected':False}
for path in paths:
    mesh=unreal.load_asset(path)
    if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError('Missing selected Fab mesh '+path)
    b=mesh.get_bounds();slots=[]
    for slot in mesh.get_editor_property('static_materials'):
        material=slot.material_interface
        if material is None:raise RuntimeError('Missing selected Fab material')
        slots.append(material.get_path_name())
        if material.get_path_name() not in result['materials']:
            parent=material
            while isinstance(parent,unreal.MaterialInstanceConstant):parent=parent.get_editor_property('parent')
            if not isinstance(parent,unreal.Material):raise RuntimeError('Missing Fab master material')
            textures={}
            for name in lib.get_texture_parameter_names(material):
                texture=lib.get_material_instance_texture_parameter_value(material,name) if isinstance(material,unreal.MaterialInstanceConstant) else lib.get_material_default_texture_parameter_value(material,name)
                textures[str(name)]={'asset':texture.get_path_name(),'virtual_streaming':bool(texture.get_editor_property('virtual_texture_streaming'))} if texture else None
            result['materials'][material.get_path_name()]={'master':parent.get_path_name(),'textures':textures}
    result['meshes'][path]={'bounds_origin':[b.origin.x,b.origin.y,b.origin.z],'bounds_extent':[b.box_extent.x,b.box_extent.y,b.box_extent.z],'lods':mesh.get_num_lods(),'triangles':[mesh.get_num_triangles(i) for i in range(mesh.get_num_lods())],'nanite':mesh.get_editor_property('nanite_settings').get_editor_property('enabled'),'materials':slots}
(ROOT/'data/native-fab-quality-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('Audited selected native Fab meshes:',len(result['meshes']))
