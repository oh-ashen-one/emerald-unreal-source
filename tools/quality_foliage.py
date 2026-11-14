"""Selected free Fab foliage, with reproducible project material derivatives."""

def prepare(unreal,eal,compile_material,report):
    base='/Game/StyleHex_Studio/Free_Packs/FREE_Stylized_Forest_Sample'
    specs={**{'fab_tree_'+str(i+1):base+'/Meshes/Trees/SM_Tree_'+name for i,name in enumerate(('Broadleaf_1','Broadleaf_2','Birch_1','Birch_2'))},
           **{'fab_grass_'+str(i):base+'/Meshes/Foliage/SM_Fol_Grass_Clump_'+str(i) for i in range(1,6)},
           **{'fab_flower_'+str(i):base+'/Meshes/Foliage/SM_Fol_Flower_Clump_'+str(i) for i in range(1,4)},
           **{'fab_bush_'+str(i):base+'/Meshes/Foliage/SM_Fol_Bush_'+str(i) for i in range(1,3)},
           **{'fab_rock_'+str(i):base+'/Meshes/Stones/SM_Stone_'+str(i) for i in range(1,4)},
           'fab_boulder':base+'/Meshes/Stones/SM_Stone_Boulder_1',
           'epic_oak':'/Game/ArchVis/SampleScene/Tree/HillTree_02'}
    meshes={};materials={};clones={};roots={};lib=unreal.MaterialEditingLibrary
    def clone(source):
        key=source.get_path_name()
        if key in clones:return clones[key]
        target='/Game/Imported/QualityFabMaterials/'+source.get_name()
        result=unreal.load_asset(target) if eal.does_asset_exist(target) else eal.duplicate_asset(key,target)
        if result is None:raise RuntimeError('Cannot duplicate licensed Fab material')
        clones[key]=result
        if isinstance(source,unreal.MaterialInstanceConstant):
            lib.set_material_instance_parent(result,clone(source.get_editor_property('parent')))
            lib.update_material_instance(result)
        elif isinstance(source,unreal.Material):
            lib.set_material_usage(result,unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES);roots[result.get_path_name()]=result
        else:raise RuntimeError('Unexpected Fab material type')
        return result
    for name,path in specs.items():
        mesh=unreal.load_asset(path)
        if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError('Acquire selected licensed Fab assets before level build: '+path)
        meshes[name]=mesh;materials[name]=[clone(s.material_interface) for s in mesh.get_editor_property('static_materials')]
    for material in roots.values():compile_material(material)
    for material in clones.values():eal.save_loaded_asset(material,only_if_is_dirty=False)
    from pathlib import Path
    from quality_grass import prepare as prepare_grass
    root=Path(unreal.Paths.project_dir()).resolve().parents[1]
    grass_meshes,grass_materials=prepare_grass(root,unreal,eal,compile_material,report)
    meshes.update(grass_meshes);materials.update(grass_materials)
    report['fab_foliage']={'source':'https://www.fab.com/listings/3c1a31b6-e523-4a0f-97d0-26b0db69b6bc','license':'Fab Standard License','selected_meshes':{k:v.get_path_name() for k,v in meshes.items() if k.startswith('fab_')},'material_derivatives':{k:v.get_path_name() for k,v in clones.items() if k.startswith('/Game/StyleHex_Studio/')},'source_cache_unchanged':True,'blueprint_gameplay_used':False}
    report['quality_tree_choice']={'asset':meshes['epic_oak'].get_path_name(),'source':'Installed UE5.8.3 ArchVis Template Examples','license':'Epic Unreal Engine EULA Examples','license_url':'https://www.unrealengine.com/eula/unreal','triangles':[meshes['epic_oak'].get_num_triangles(i) for i in range(meshes['epic_oak'].get_num_lods())],'materials':[m.get_path_name() for m in materials['epic_oak']],'reason':'Fab sample tree materials use default flat leaf normals; testing existing licensed professional tree with real leaf/bark normal bindings. Fab foliage and environment dressing remain in use; full Fab native-pack download control remains unresolved.'}
    return meshes,materials


def scatter(unreal,spawn_owned,meshes,materials,map_data,report):
    import random,math
    rng=random.Random(20261113);g=map_data['geometry'];actors={};components={};counts={}
    from quality_ground_plan import build as plan_ground,distance as ground_distance
    wear=plan_ground(map_data)
    def component(name,context=False):
        key=(name,context)
        if key not in components:
            actor=spawn_owned(unreal.load_class(None,'/Script/Emerald.EmeraldFoliageCluster'),unreal.Vector(0,0,0));actor.set_actor_label(('Context_' if context else 'SourceFoliage_')+name)
            tags=[unreal.Name('EmeraldGenerated')]
            if context:tags.append(unreal.Name('EmeraldBackdrop'))
            actor.set_editor_property('tags',tags)
            comp=actor.get_component_by_class(unreal.HierarchicalInstancedStaticMeshComponent)
            if comp is None:raise RuntimeError('Native serialized foliage component missing')
            comp.set_static_mesh(meshes[name]);comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            for i,mat in enumerate(materials[name]):comp.set_material(i,mat)
            comp.set_editor_property('instance_start_cull_distance',18000 if context else 12000);comp.set_editor_property('instance_end_cull_distance',30000 if context else 20000)
            components[key]=comp;actors[key]=actor;counts[key]=0
        return components[key]
    def instance(name,x,y,height,z=0,context=False,yaw=None):
        mesh=meshes[name];b=mesh.get_bounds();scale=height/max(2*b.box_extent.z,.001);angle=rng.uniform(0,360) if yaw is None else yaw;a=math.radians(angle)
        ox,oy=b.origin.x*scale,b.origin.y*scale
        loc=unreal.Vector(x-ox*math.cos(a)+oy*math.sin(a),y-ox*math.sin(a)-oy*math.cos(a),z-(b.origin.z-b.box_extent.z)*scale)
        transform=unreal.Transform(location=loc,rotation=unreal.Rotator(pitch=0,yaw=angle,roll=0),scale=unreal.Vector(scale,scale,scale))
        component(name,context).add_instance(transform,world_space=True);counts[(name,context)]+=1
    flower_cells=0
    for c in g['cells']:
        x,y=c['x']*200,c['y']*200
        if c['metatile_id']==1 and not c['collision']:
            for i in range(24):
                px,py=x+rng.uniform(-92,92),y+rng.uniform(-92,92)
                if ground_distance(wear,px,py)<70:continue
                instance('fab_grass_'+str(1+rng.randrange(8)),px,py,rng.uniform(30,44))
        elif c['metatile_id']==4:
            flower_cells+=1
            for i in range(6):instance('fab_flower_'+str(1+rng.randrange(3)),x+rng.uniform(-50,50),y+rng.uniform(-50,50),rng.uniform(16,24))
    # Context remains outside the original playable grid and adds no collision.
    from build_quality_terrain import height as terrain_height
    for y in range(-8500,12500,700):
        for x in range(-8500,12500,700):
            if -650<x<4450 and -650<y<4450:continue
            if y<0 and abs(x-2000)<450:continue
            if rng.random()<.35:continue
            px,py=x+rng.uniform(-150,150),y+rng.uniform(-150,150)
            rng.randrange(4) # Retain the same deterministic placement/height stream.
            instance('epic_oak',px,py,rng.uniform(850,1300),terrain_height(px-1900,py-1900),True)
    for i in range(28):
        angle=rng.uniform(0,math.tau);radius=rng.uniform(3500,10000);x,y=1900+math.cos(angle)*radius,1900+math.sin(angle)*radius
        instance('fab_rock_'+str(1+rng.randrange(3)),x,y,rng.uniform(100,230),terrain_height(x-1900,y-1900),True)
    values={('context_' if context else '')+name:number for (name,context),number in counts.items()}
    for key,comp in components.items():
        actors[key].finalize_instances()
        if comp.get_instance_count()!=counts[key]:raise RuntimeError('Native foliage instance count differs from plan')
    report['fab_foliage_scatter']={'instances':values,'source_flower_cells':flower_cells,'source_grass_cells':sum(c['metatile_id']==1 and not c['collision'] for c in g['cells']),'collision':'Disabled; original cell data unchanged','context':'Outside canonical grid only','seed':20261113}
    return values
