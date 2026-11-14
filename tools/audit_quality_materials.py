"""Inspect actual native material parameter inheritance and mesh rendering paths."""
import json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve().parents[1];lib=unreal.MaterialEditingLibrary
report={'materials':{},'meshes':{}}
paths=['/Game/Imported/Materials/SourceRoofPBR','/Game/Imported/Materials/MI_Roof_PBR','/Game/Imported/Materials/MI_LabRoof_PBR','/Game/Imported/Materials/Quality_leafy_grass','/Game/Imported/Materials/Quality_white_planks_clean','/Game/ArchVis/SampleScene/Tree/Materials/M_HillTree_01_Leaves','/Game/Imported/QualityFabMaterials/MI_Tree_Leaves_Broadleaf','/Game/Imported/QualityFabMaterials/MI_Tree_Leaves_Birch_A']
for file in ('native-quality-furniture-import-report.json','native-quality-architecture-import-report.json','native-quality-fixture-report.json'):
    for row in json.loads((ROOT/'data'/file).read_text()).values():paths.extend(row['materials'])
for path in dict.fromkeys(paths):
    material=unreal.load_asset(path);row={'class':material.get_class().get_name(),'textures':{},'scalars':{},'vectors':{}}
    instance=isinstance(material,unreal.MaterialInstanceConstant)
    parent=material;row['instance_chain']=[]
    while isinstance(parent,unreal.MaterialInstanceConstant):
        overrides=parent.get_editor_property('base_property_overrides')
        row['instance_chain'].append({'asset':parent.get_path_name(),'blend_override':overrides.get_editor_property('override_blend_mode'),'blend_mode':str(overrides.get_editor_property('blend_mode'))})
        parent=parent.get_editor_property('parent')
    row['parent']=parent.get_path_name();row['parent_blend_mode']=str(parent.get_editor_property('blend_mode'))
    if instance:
        overrides=material.get_editor_property('base_property_overrides')
        row['blend_override']={'enabled':overrides.get_editor_property('override_blend_mode'),'blend_mode':str(overrides.get_editor_property('blend_mode'))}
        row['switches']={str(n):lib.get_material_instance_static_switch_parameter_value(material,n) for n in lib.get_static_switch_parameter_names(material)}
    for name in lib.get_texture_parameter_names(material):
        texture=lib.get_material_instance_texture_parameter_value(material,name) if instance else lib.get_material_default_texture_parameter_value(material,name)
        row['textures'][str(name)]=texture.get_path_name() if texture else None
    for name in lib.get_scalar_parameter_names(material):row['scalars'][str(name)]=lib.get_material_instance_scalar_parameter_value(material,name) if instance else lib.get_material_default_scalar_parameter_value(material,name)
    for name in lib.get_vector_parameter_names(material):
        color=lib.get_material_instance_vector_parameter_value(material,name) if instance else lib.get_material_default_vector_parameter_value(material,name);row['vectors'][str(name)]=[color.r,color.g,color.b,color.a]
    report['materials'][path]=row
for path in ['/Game/ArchVis/SampleScene/Tree/HillTree_02','/Game/Imported/QualityTerrain/SourceTerrain/StaticMeshes/SourceTerrain']:
    mesh=unreal.load_asset(path);report['meshes'][path]={'nanite':mesh.get_editor_property('nanite_settings').get_editor_property('enabled'),'lods':mesh.get_num_lods(),'triangles':[mesh.get_num_triangles(i) for i in range(mesh.get_num_lods())]}
(ROOT/'out/quality-material-readback.json').write_text(json.dumps(report,indent=2)+'\n');print('Audited native material inheritance/parameters:',len(report['materials']),'materials;',len(report['meshes']),'meshes')
