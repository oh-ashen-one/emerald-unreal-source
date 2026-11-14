"""Original procedural decorative paper and ceramic; no source-game bitmaps."""
from material_graph import clear_material


def build_map_print(unreal,eal,tools,compile_material):
    lib=unreal.MaterialEditingLibrary;path='/Game/Imported/Materials/RegionPrint'
    mat=unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset('RegionPrint','/Game/Imported/Materials',unreal.Material,unreal.MaterialFactoryNew())
    clear_material(mat,unreal)
    uv=lib.create_material_expression(mat,unreal.MaterialExpressionTextureCoordinate,0,0)
    code='float2 p=(UV-.5)*float2(1.5,1); float coast=.29-length(p*float2(.8,1.1))+.035*sin(p.x*28)+.025*cos(p.y*24); float land=smoothstep(-.012,.012,coast); float3 c=lerp(float3(.10,.27,.37),float3(.54,.64,.39),land); float2 g=abs(frac(UV*8)-.5); float gridLine=1-smoothstep(.01,.025,min(g.x,g.y)); c=lerp(c,float3(.78,.79,.61),gridLine*.23); float border=step(.035,min(min(UV.x,1-UV.x),min(UV.y,1-UV.y))); return lerp(float3(.75,.70,.53),c,border);'
    custom=lib.create_material_expression(mat,unreal.MaterialExpressionCustom,0,0);i=unreal.CustomInput();i.set_editor_property('input_name','UV');custom.set_editor_property('inputs',[i]);custom.set_editor_property('code',code);custom.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    if not lib.connect_material_expressions(uv,'',custom,'UV') or not lib.connect_material_property(custom,'',unreal.MaterialProperty.MP_BASE_COLOR):raise RuntimeError('Original decorative map material disconnected')
    rough=lib.create_material_expression(mat,unreal.MaterialExpressionConstant,0,0);rough.set_editor_property('r',.82);lib.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
    compile_material(mat);eal.save_loaded_asset(mat,only_if_is_dirty=False);return mat


def build_lab_tiles(unreal,eal,tools,compile_material):
    lib=unreal.MaterialEditingLibrary;path='/Game/Imported/Materials/SourceLabTile'
    mat=unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset('SourceLabTile','/Game/Imported/Materials',unreal.Material,unreal.MaterialFactoryNew())
    clear_material(mat,unreal);position=lib.create_material_expression(mat,unreal.MaterialExpressionWorldPosition,0,0)
    def custom(code,kind,prop):
        node=lib.create_material_expression(mat,unreal.MaterialExpressionCustom,0,0);i=unreal.CustomInput();i.set_editor_property('input_name','P');node.set_editor_property('inputs',[i]);node.set_editor_property('code',code);node.set_editor_property('output_type',kind)
        if not lib.connect_material_expressions(position,'',node,'P') or not lib.connect_material_property(node,'',prop):raise RuntimeError('Procedural ceramic graph disconnected')
    custom('float2 e=min(frac(P.xy/100),1-frac(P.xy/100))*100; float t=smoothstep(.4,1.5,min(e.x,e.y)); float h=frac(sin(dot(floor(P.xy/100),float2(12.9898,78.233)))*43758.5453); return lerp(float3(.13,.20,.21),float3(.51,.63,.64)*(1+.035*(h-.5)),t);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,unreal.MaterialProperty.MP_BASE_COLOR)
    custom('float2 f=frac(P.xy/100),e=min(f,1-f)*100; float q=saturate((min(e.x,e.y)-.4)/1.1); float d=.20*6*q*(1-q)/1.1; float2 s=-sign(f-.5); float2 slope=e.x<e.y?float2(d*s.x,0):float2(0,d*s.y); return normalize(float3(-slope,1));',unreal.CustomMaterialOutputType.CMOT_FLOAT3,unreal.MaterialProperty.MP_NORMAL)
    custom('return .44+.045*frac(sin(dot(floor(P.xy/100),float2(12.9898,78.233)))*43758.5453);',unreal.CustomMaterialOutputType.CMOT_FLOAT1,unreal.MaterialProperty.MP_ROUGHNESS)
    mat.set_editor_property('tangent_space_normal',False);lib.set_material_usage(mat,unreal.MaterialUsage.MATUSAGE_NANITE);compile_material(mat);eal.save_loaded_asset(mat,only_if_is_dirty=False);return mat
