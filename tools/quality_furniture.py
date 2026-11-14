"""Import complete PBR furniture and adapt only its source-grid presentation."""
import json

def prepare(root,unreal,eal,tools,compile_material,report):
    meshes={};materials={};rows={}
    for item in json.loads((root/'data/quality-furniture-lock.json').read_text())['assets']:
        name=item['id'];task=unreal.AssetImportTask()
        for key,value in [('filename',str(root/item['baked_file'])),('destination_path','/Game/Imported/QualityFurniture/'+name),('destination_name',name),('automated',True),('save',True),('replace_existing',True)]:task.set_editor_property(key,value)
        tools.import_asset_tasks([task])
        imported=[unreal.load_asset(p) for p in task.get_editor_property('imported_object_paths') if isinstance(unreal.load_asset(p),unreal.StaticMesh)]
        if len(imported)!=1:raise RuntimeError('Furniture must import as one complete scene')
        mesh=imported[0];settings=mesh.get_editor_property('nanite_settings');settings.set_editor_property('enabled',False);mesh.set_editor_property('nanite_settings',settings);eal.save_loaded_asset(mesh,only_if_is_dirty=False)
        if mesh.get_num_triangles(0)!=item['triangles']:raise RuntimeError('Furniture full geometry count differs: '+name)
        mats=[s.material_interface for s in mesh.get_editor_property('static_materials')];parents={}
        for mat in mats:
            if mat is None:raise RuntimeError('Furniture material missing')
            parent=mat
            while isinstance(parent,unreal.MaterialInstanceConstant):parent=parent.get_editor_property('parent')
            parents[parent.get_path_name()]=parent
        for parent in parents.values():compile_material(parent)
        key='quality_'+name;meshes[key]=mesh;materials[key]=mats;b=mesh.get_bounds()
        rows[name]={'mesh':mesh.get_path_name(),'triangles_lod0':mesh.get_num_triangles(0),'materials':[m.get_path_name() for m in mats],'bounds_extent':[b.box_extent.x,b.box_extent.y,b.box_extent.z],'source':item['url'],'license':item['license']}
    report['quality_furniture_imports']=rows;(root/'data/native-quality-furniture-import-report.json').write_text(json.dumps(rows,indent=2)+'\n')
    return meshes,materials

def replacement(item):
    name=item['id'];asset=item['asset'];yaw=item['yaw'];size=list(item['size_cm'])
    if asset=='gamingConsole':return 'fixture_gaming_console',size,yaw
    if asset=='kitchenStoveElectric':return 'fixture_electric_stove',size,yaw
    if asset=='specimenAnalyzer':return 'fixture_specimen_analyzer',size,yaw+180
    if asset=='analyzerController':return 'fixture_analyzer_controller',size,yaw+180
    if asset=='computerTerminal':return 'fixture_fab_retrocomputer',size,yaw
    if asset=='kitchenSink':return 'fixture_fab_sink',size,yaw
    if asset=='stairs':return 'fixture_fab_stairs',size,yaw
    if asset=='plantSmall1':return 'fixture_potted_plant_01',size,yaw
    if asset=='kitchenFridgeSmall':return 'fixture_fab_fridge',[size[1],size[0],size[2]],yaw-90
    if asset=='televisionVintage':return 'fixture_television_02',size,yaw
    if asset=='desk' or name.startswith('SourcePC_'):return 'fixture_metal_office_desk',size,yaw
    if name.startswith(('SourceLivingTable_','SourceNotebookDesk_')):return 'fixture_small_wooden_table_01',size,yaw
    if name.startswith('SourceKitchenCupboard_'):return 'fixture_painted_wooden_cabinet_02',size,yaw
    if asset=='cardboardBoxClosed':return 'fixture_cardboard_box_01',size,yaw
    if asset=='books':return ('fixture_book_encyclopedia_set_01' if 'SourceShelfBooks' in name else 'fixture_book_stack'),size,yaw
    # Source kit fronts oppose Kenney's convention; inspected game view showed
    # backs facing the table until this explicit half turn.
    if asset=='chairModernCushion':
        # Existing110x130cm source footprint/anchor/facing are retained. The
        # earlier150cm height vertically squashed the complete scanned chair
        # and left adult seated poses above its cushion.250cm restores its
        # proportions and matches the measured adult pelvis/cushion height.
        size[2]=250
        return 'quality_dining_chair_02',size,yaw+180
    if name.startswith('SourceDiningTable_'):return 'quality_round_wooden_table_01',size,yaw
    if name.startswith('SourceBed_'):
        # The complete day bed's long native X axis turns onto the original
        # two-cell Y footprint. Exchange local dimensions before rotating.
        return 'quality_vintage_day_bed',[size[1],size[0],size[2]],-90
    if name.startswith('SourceLabBookshelf_'):return 'quality_wooden_bookshelf_worn',size,yaw
    return None
