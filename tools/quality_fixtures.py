"""Native complete fixture import and PBR binding checks."""
import json

def source_geometry_counts(path):
    """Verify exact coincident-corner cleanup after native float32/cm conversion."""
    import struct
    raw=path.read_bytes();offset=12;doc=None;binary=b''
    while offset<len(raw):
        size,kind=struct.unpack_from('<II',raw,offset);chunk=raw[offset+8:offset+8+size];offset+=8+size
        if kind==0x4e4f534a:doc=json.loads(chunk)
        elif kind==0x004e4942:binary=chunk
    def read(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        code={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']];width=3 if a['type']=='VEC3' else 1
        fmt='<'+code*width;size=struct.calcsize(fmt);start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',size)
        return [struct.unpack_from(fmt,binary,start+i*stride) for i in range(a['count'])]
    total=0;collapsed=0
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            positions=[tuple(struct.unpack('<f',struct.pack('<f',x*100))[0] for x in vertex) for vertex in read(primitive['attributes']['POSITION'])];indices=[x[0] for x in read(primitive['indices'])]
            for i in range(0,len(indices),3):
                a,b,c=(positions[j] for j in indices[i:i+3])
                total+=1;collapsed+=int(a==b or a==c or b==c)

    return total,collapsed

def prepare(root,unreal,eal,tools,compile_material,report):
    meshes={};materials={};rows={};lib=unreal.MaterialEditingLibrary
    old_path=root/'data/native-quality-fixture-report.json';old=json.loads(old_path.read_text()) if old_path.exists() else {}
    items=json.loads((root/'data/quality-fixture-lock.json').read_text())['assets']
    furnishing_variants=root/'data/furnishing-variants-report.json'
    if furnishing_variants.exists():items+=json.loads(furnishing_variants.read_text())['assets']
    interior_details=root/'data/interior-detail-report.json'
    if interior_details.exists():items+=json.loads(interior_details.read_text())['assets']
    original=root/'data/original-lab-analyzer-report.json'
    if original.exists():items+=json.loads(original.read_text())['assets']
    for item in items:
        name=item['id'];prior=old.get(name,{})
        if prior.get('converted_sha256')==item['baked']['sha256'] and eal.does_asset_exist(prior.get('mesh','/Missing')):mesh=unreal.load_asset(prior['mesh'])
        else:
            task=unreal.AssetImportTask()
            for key,value in [('filename',str(root/item['baked_file'])),('destination_path','/Game/Imported/QualityFixtures/'+name),('destination_name',name),('automated',True),('save',True),('replace_existing',True)]:task.set_editor_property(key,value)
            tools.import_asset_tasks([task]);found=[unreal.load_asset(p) for p in task.get_editor_property('imported_object_paths') if isinstance(unreal.load_asset(p),unreal.StaticMesh)]
            if len(found)!=1:raise RuntimeError('Expected one complete fixture assembly '+name)
            mesh=found[0]
        settings=mesh.get_editor_property('nanite_settings');settings.set_editor_property('enabled',False);mesh.set_editor_property('nanite_settings',settings);eal.save_loaded_asset(mesh,only_if_is_dirty=False)
        mats=[s.material_interface for s in mesh.get_editor_property('static_materials')];parents={};bindings={}
        material_adapters=[]
        if item.get('texture_token')=='metal_plate_02':
            # Embedded glTF imports can retain generic texture_N names across
            # reimport. Bind separately pinned scan maps and verify the actual
            # material instance values, independently of those generated names.
            scans={};folder='/Game/Imported/QualityFixtures/ScannedMetal';eal.make_directory(folder)
            for f in json.loads((root/'data/lab-metal-lock.json').read_text())['files']:
                label='metal_plate_02_'+f['channel'];path=folder+'/'+label
                if not eal.does_asset_exist(path):
                    task=unreal.AssetImportTask()
                    for k,v in [('filename',str(root/f['path'])),('destination_path',folder),('destination_name',label),('automated',True),('save',True)]:task.set_editor_property(k,v)
                    tools.import_asset_tasks([task])
                texture=unreal.load_asset(path)
                if not isinstance(texture,unreal.Texture2D):raise RuntimeError('Pinned original scan texture missing')
                texture.set_editor_property('srgb',f['channel']=='diff');texture.set_editor_property('virtual_texture_streaming',False)
                if f['channel']=='nor_gl':texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP);texture.set_editor_property('flip_green_channel',True)
                eal.save_loaded_asset(texture,only_if_is_dirty=False);scans[f['channel']]=texture
            for mat in mats:
                if not isinstance(mat,unreal.MaterialInstanceConstant):raise RuntimeError('Expected original fixture material instance')
                for key,channel in [('BaseColorTexture','diff'),('NormalTexture','nor_gl'),('MetallicRoughnessTexture','arm'),('OcclusionTexture','arm')]:
                    if key=='OcclusionTexture' and key not in [str(n) for n in lib.get_texture_parameter_names(mat)]:continue
                    lib.set_material_instance_texture_parameter_value(mat,key,scans[channel])
                    if lib.get_material_instance_texture_parameter_value(mat,key)!=scans[channel]:raise RuntimeError('Original fixture scan binding readback differs')
                lib.update_material_instance(mat);eal.save_loaded_asset(mat,only_if_is_dirty=False)
            from original_lab_materials import adapt
            material_adapters=adapt(root,unreal,eal,tools,compile_material,mesh,scans)
            mats=[s.material_interface for s in mesh.get_editor_property('static_materials')]
        for mat in mats:
            if mat is None:raise RuntimeError('Fixture material absent')
            parent=mat
            while isinstance(parent,unreal.MaterialInstanceConstant):parent=parent.get_editor_property('parent')
            parents[parent.get_path_name()]=parent;bindings[mat.get_path_name()]={}
            for parameter in lib.get_texture_parameter_names(mat):
                texture=lib.get_material_instance_texture_parameter_value(mat,parameter) if isinstance(mat,unreal.MaterialInstanceConstant) else lib.get_material_default_texture_parameter_value(mat,parameter)
                bindings[mat.get_path_name()][str(parameter)]=texture.get_path_name() if texture else None
        for parent in parents.values():compile_material(parent)
        source_triangles,collapsed=source_geometry_counts(root/item['baked_file'])
        if source_triangles!=item['baked']['triangles']:raise RuntimeError('Pinned fixture triangle count differs '+name)
        if mesh.get_num_triangles(0)!=source_triangles-collapsed:raise RuntimeError('Full native fixture geometry differs '+name+': actual='+str(mesh.get_num_triangles(0))+' expected='+str(source_triangles-collapsed)+' collapsed_corners='+str(collapsed)+' nanite='+str(mesh.get_editor_property('nanite_settings').get_editor_property('enabled')))
        token=item.get('texture_token',name)
        required=('BaseColorTexture','NormalTexture','MetallicRoughnessTexture')
        if not any(all(token in str(values.get(key,'')) for key in required) for values in bindings.values()):raise RuntimeError('Actual fixture material-instance scan bindings absent '+name)
        key='fixture_'+name;meshes[key]=mesh;materials[key]=mats;b=mesh.get_bounds()
        rows[name]={'mesh':mesh.get_path_name(),'triangles':mesh.get_num_triangles(0),'source_triangles':source_triangles,'removed_coincident_corner_triangles':collapsed,'source_parts':item['baked']['source_mesh_instances'],'converted_sha256':item['baked']['sha256'],'materials':[m.get_path_name() for m in mats],'texture_bindings':bindings,'bounds_origin':[b.origin.x,b.origin.y,b.origin.z],'bounds_extent':[b.box_extent.x,b.box_extent.y,b.box_extent.z],'source':item['url'],'license':item['license'],'scope':'Complete native geometry/PBR readback excluding exactly counted faces with coincident native corners; rendered facing/fit and final quality require inspection'}
        if material_adapters:rows[name]['project_material_adapters']=material_adapters
    old_path.write_text(json.dumps(rows,indent=2)+'\n');report['quality_fixtures']=rows
    return meshes,materials
