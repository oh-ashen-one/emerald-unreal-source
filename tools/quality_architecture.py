"""Complete native imports of selected licensed high-detail architectural pieces."""
import json


def prepare(root,unreal,eal,tools,compile_material,report):
    meshes={};materials={};lib=unreal.MaterialEditingLibrary;rows={}
    specifications=[('quixel_window','OldWoodenWindow',20816),('quixel_door','OldWoodenDoor',7795)]
    for key,name,expected in specifications:
        source=root/'unreal/Emerald/Content/Imported/QualitySources'/(name+'.glb')
        task=unreal.AssetImportTask()
        for field,value in [('filename',str(source)),('destination_path','/Game/Imported/Architecture/'+name),('destination_name',name),('automated',True),('save',True),('replace_existing',True)]:task.set_editor_property(field,value)
        tools.import_asset_tasks([task])
        imported=[unreal.load_asset(p) for p in task.get_editor_property('imported_object_paths') if isinstance(unreal.load_asset(p),unreal.StaticMesh)]
        if len(imported)!=1:raise RuntimeError('Native architectural import must preserve one complete baked scene')
        mesh=imported[0];settings=mesh.get_editor_property('nanite_settings');settings.set_editor_property('enabled',False);mesh.set_editor_property('nanite_settings',settings);eal.save_loaded_asset(mesh,only_if_is_dirty=False)
        mats=[slot.material_interface for slot in mesh.get_editor_property('static_materials')]
        roots={}
        for mat in mats:
            if mat is None:raise RuntimeError('Architectural material missing')
            parent=mat
            while isinstance(parent,unreal.MaterialInstanceConstant):parent=parent.get_editor_property('parent')
            roots[parent.get_path_name()]=parent
        for parent in roots.values():compile_material(parent)
        count=mesh.get_num_triangles(0)
        if expected is not None and count!=expected:raise RuntimeError('Native high-detail window geometry incomplete')
        b=mesh.get_bounds();meshes[key]=mesh;materials[key]=mats;rows[key]={'mesh':mesh.get_path_name(),'triangles_lod0':count,'bounds_origin':[b.origin.x,b.origin.y,b.origin.z],'bounds_extent':[b.box_extent.x,b.box_extent.y,b.box_extent.z],'materials':[m.get_path_name() for m in mats],'nanite':False}
    base='/Game/Fantastic_Village_Pack/'
    for key,path in [('village_chimney','meshes/buildings/SM_BLD_chimney_v01_01'),('village_fence','meshes/props/construction/SM_PROP_fence_v01_01'),('village_sign','meshes/props/deco/SM_PROP_sign_01')]:
        mesh=unreal.load_asset(base+path)
        if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError('Selected native village part unavailable')
        meshes[key]=mesh;materials[key]=[s.material_interface for s in mesh.get_editor_property('static_materials')]
        for mat in materials[key]:
            parent=mat
            while isinstance(parent,unreal.MaterialInstanceConstant):parent=parent.get_editor_property('parent')
            compile_material(parent)
        b=mesh.get_bounds();rows[key]={'mesh':mesh.get_path_name(),'triangles_lod0':mesh.get_num_triangles(0),'bounds_origin':[b.origin.x,b.origin.y,b.origin.z],'bounds_extent':[b.box_extent.x,b.box_extent.y,b.box_extent.z],'materials':[m.get_path_name() for m in materials[key]]}
    report['quality_architecture_imports']=rows
    (root/'data/native-quality-architecture-import-report.json').write_text(json.dumps(rows,indent=2)+'\n')
    return meshes,materials


def panel_shell(box,center_x,center_y,width,front_y,openings):
    # Preserve the former source footprint, but build wall volumes around real
    # door/window openings instead of hiding them against a solid body cube.
    left,right=center_x-width*.5,center_x+width*.5;back=center_y-300;thickness=28;height=380
    box([center_x,back+thickness*.5,height*.5],[width,thickness,height],'WallSiding','SourceShellBack')
    for x in (left+thickness*.5,right-thickness*.5):box([x,center_y,height*.5],[thickness,600,height],'WallSiding','SourceShellSide')
    cuts=sorted({left,right,*[max(left,min(right,o[0]+s*o[1]*.5)) for o in openings for s in (-1,1)]})
    for a,b in zip(cuts,cuts[1:]):
        if b-a<.01:continue
        mid=(a+b)*.5;active=next((o for o in openings if abs(mid-o[0])<o[1]*.5),None)
        bands=[(0,height)] if active is None else [(0,active[2]),(active[3],height)]
        for bottom,top in bands:
            if top-bottom>.01:box([mid,front_y-thickness*.5,(bottom+top)*.5],[b-a,thickness,top-bottom],'WallSiding','SourceFacadePanel')
    box([center_x,center_y,4],[width-2*thickness,600-2*thickness,8],'WoodFloor','SourceShellInteriorFloor')
    # Painted plinth and fascia retain the source outline and make the opening
    # edges read in the real perspective view. Licensed scan PBR stays shared.
    for y in (back,front_y):
        if abs(y-front_y)<.01:
            door=next(o for o in openings if o[2]==0);a,b=door[0]-door[1]*.5,door[0]+door[1]*.5
            for lo,hi in ((left,a),(b,right)):
                if hi>lo:box([(lo+hi)*.5,y,20],[hi-lo,35,40],'Cream','SourcePlinth')
        else:box([center_x,y,20],[width+10,35,40],'Cream','SourcePlinth')
        box([center_x,y,365],[width+20,34,30],'Cream','SourceFascia')
    for x in (left,right):
        box([x,center_y,20],[35,600,40],'Cream','SourcePlinthSide')
        box([x,center_y,365],[34,600,30],'Cream','SourceFasciaSide')


def place_piece(prop,meshes,materials,key,x,y,width,height,label,z=0,depth=24):
    b=meshes[key].get_bounds()
    # The thin horizontal axis is the native face normal; adapt both glTF and
    # native kit conventions explicitly, preserving upright Z and source anchor.
    if b.box_extent.x<b.box_extent.y:
        actor=prop(key,x,y,depth,width,height,90,label=label,z=z)
    else:actor=prop(key,x,y,width,depth,height,0,label=label,z=z)
    for i,material in enumerate(materials[key]):actor.static_mesh_component.set_material(i,material)
    return actor
