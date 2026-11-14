"""Camera-aware room shell from source bounds and existing licensed finishes."""
def build(root,unreal,eal,tools,palette,box,prop,spawn,recolor,m):
    g=m['geometry'];width=g['width']*200;depth=g['height']*200;cx=(g['width']-1)*100;cy=(g['height']-1)*100
    actors=[];lights=[]
    def gated(actor):
        actor.set_editor_property('tags',[unreal.Name('EmeraldGenerated'),unreal.Name('EmeraldThirdPersonOnly')]);actor.set_actor_hidden_in_game(True)
        if isinstance(actor,unreal.StaticMeshActor):
            component=actor.static_mesh_component;component.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY);component.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_IGNORE);component.set_collision_response_to_channel(unreal.CollisionChannel.ECC_CAMERA,unreal.CollisionResponseType.ECR_BLOCK)
            if component.get_collision_enabled()!=unreal.CollisionEnabled.QUERY_ONLY or component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_CAMERA)!=unreal.CollisionResponseType.ECR_BLOCK or component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)!=unreal.CollisionResponseType.ECR_IGNORE:raise RuntimeError('Room camera-only collision readback differs')
        actors.append(actor.get_actor_label());return actor
    # Complete the existing wall footprint upward; retain overhead cutaways.
    gated(box([cx,-70,435],[width+60,80,130],'WallSiding','PerspectiveBackUpperWall'))
    for x in (-110,width-90):gated(box([x,cy,330],[36,depth,340],'WallSiding','PerspectiveSideUpperWall_'+str(x)))
    gated(box([cx,cy,510],[width+60,depth+60,20],'WallSiding','PerspectiveCeiling'))
    # The front wall follows the outer boundary; keep openings at actual source
    # exit columns. No geometry or lighting changes source grid collision.
    exits=sorted({w['x']*200 for w in m['warp_events'] if w['y']>=g['height']-2})
    start=-100
    for end,next_start in [(x-120,x+120) for x in exits]+[(width-100,width-100)]:
        if end>start:gated(box([(start+end)/2,depth-90,250],[end-start,36,500],'WallSiding','PerspectiveFrontWall_'+str(start)))
        start=next_start
    for x in exits:gated(box([x,depth-90,445],[240,36,110],'WallSiding','PerspectiveDoorLintel_'+str(x)))
    guard=gated(box([cx,depth-90,250],[width,36,500],'WallSiding','PerspectiveDoorCameraGuard'));guard.static_mesh_component.set_visibility(False);guard.static_mesh_component.set_editor_property('cast_shadow',False);guard.static_mesh_component.set_editor_property('affect_distance_field_lighting',False)
    # Stepped crown profiles give the ceiling a physical edge at the old walls.
    for z,size in [(470,14),(483,10),(493,6)]:
        for y in (-18,depth-114):gated(box([cx,y,z],[width,size,size],'Trim',f'PerspectiveCrownY_{y}_{z}'))
        for x in (-84,width-116):gated(box([x,cy,z],[size,depth,size],'Trim',f'PerspectiveCrownX_{x}_{z}'))
    lab='Lab' in m['name'];lib=unreal.MaterialEditingLibrary;folder='/Game/Imported/Materials';name='RoomLabLight' if lab else 'RoomWarmLight';path=folder+'/'+name
    glow=unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset(name,folder,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
    parent=unreal.load_asset('/Game/Imported/QualityFixtures/OriginalLabMaterials/M_LabDisplay')
    if not isinstance(parent,unreal.Material):raise RuntimeError('Verified scanned microdetail light parent missing')
    lib.set_material_instance_parent(glow,parent);lib.set_material_instance_vector_parameter_value(glow,'EmissiveColor',unreal.LinearColor(.9,.95,1,1) if lab else unreal.LinearColor(1,.88,.72,1));lib.set_material_instance_scalar_parameter_value(glow,'EmissiveStrength',4000.)
    if abs(lib.get_material_instance_scalar_parameter_value(glow,'EmissiveStrength')-4000)>1e-3:raise RuntimeError('Room fixture emission readback differs')
    lib.update_material_instance(glow);eal.save_loaded_asset(glow,only_if_is_dirty=False);palette['RoomWarmLight']=glow
    count=3 if lab else 2;temperature=6500. if lab else 4000.
    for iy in range(count):
        for ix in range(count):
            x=-100+width*(ix+.5)/count;y=-100+depth*(iy+.5)/count
            fixture=gated(prop('lampSquareCeiling',x,y,140,140,20,label=f'PerspectiveCeilingFixture_{ix}_{iy}',z=475))
            recolor(fixture,[('lamp','RoomWarmLight'),('metal','WallSiding')])
            light=spawn(unreal.RectLight,unreal.Vector(x,y,468),unreal.Rotator(pitch=-90,yaw=0,roll=0))
            light.set_actor_label(f'PerspectiveRoomLight_{ix}_{iy}');gated(light);component=light.get_component_by_class(unreal.RectLightComponent)
            component.set_mobility(unreal.ComponentMobility.MOVABLE);component.set_editor_property('intensity_units',unreal.LightUnits.LUMENS);component.set_editor_property('intensity',25000.)
            component.set_editor_property('source_width',125.);component.set_editor_property('source_height',125.);component.set_editor_property('attenuation_radius',max(width,depth)*1.5)
            component.set_editor_property('use_temperature',True);component.set_editor_property('temperature',temperature);component.set_visibility(False)
            if abs(component.get_editor_property('intensity')-25000)>1e-3 or component.get_editor_property('visible'):raise RuntimeError('Room local light defaults differ')
            lights.append({'actor':light.get_actor_label(),'lumens':25000,'temperature_kelvin':temperature,'source_cm':[125,125],'position_cm':[x,y,468]})
    return {'ceiling_height_cm':500,'source_grid_unchanged':True,'source_outer_bounds_cm':[-100,-100,width-100,depth-100],'third_person_only_actors':actors,'local_lights':lights,'camera_collision':'Query-only CAMERA block; every gameplay/physics channel ignored; invisible front guard covers door gaps for camera only','finishes':'Existing licensed scanned WhitePlanksClean PBR, existing trim and complete CC0 Kenney lampSquareCeiling with project scanned-microdetail emitter','scope':'Saved architecture/light readbacks only; actual overhead/perspective render and source traversal require inspection'}
