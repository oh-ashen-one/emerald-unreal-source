"""Native, physical-scale PBR materials from locked licensed scans."""
import json
from material_graph import clear_material


def build(root,unreal,assets,tools,import_surface,palette):
    lib=unreal.MaterialEditingLibrary
    lock=json.loads((root/'data/quality-surface-lock.json').read_text())
    report={}
    for name,key,tint in [('leafy_grass','Grass',(.70,1.10,.55,1)),('brown_mud_leaves_01','QualitySoil',(1,1,1,1)),('white_planks_clean','WallSiding',(1,1,1,1))]:
        item=lock['surfaces'][name];textures={}
        for f in item['files']:
            texture=import_surface(root/f['path'],'Quality_'+name+'_'+f['channel'])
            if f['channel']!='Diffuse':texture.set_editor_property('srgb',False)
            if f['channel']=='nor_dx':texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
            if f['channel']=='arm':texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
            assets.save_loaded_asset(texture);textures[f['channel']]=texture
        target='/Game/Imported/Materials/Quality_'+name
        mat=unreal.load_asset(target) if assets.does_asset_exist(target) else tools.create_asset('Quality_'+name,'/Game/Imported/Materials',unreal.Material,unreal.MaterialFactoryNew())
        clear_material(mat,unreal)
        def node(cls):return lib.create_material_expression(mat,cls,0,0)
        def link(a,out,b,pin):
            if not lib.connect_material_expressions(a,out,b,pin):raise RuntimeError('Quality PBR input connection failed: '+pin)
        def output(n,pin,prop):
            if not lib.connect_material_property(n,pin,prop):raise RuntimeError('Quality PBR output connection failed')
        def custom(code,inputs,kind):
            n=node(unreal.MaterialExpressionCustom);n.set_editor_property('code',code);n.set_editor_property('output_type',kind)
            records=[]
            for field in inputs:
                r=unreal.CustomInput();r.set_editor_property('input_name',field);records.append(r)
            n.set_editor_property('inputs',records)
            for field,source in inputs.items():link(source,'',n,field)
            return n
        world=node(unreal.MaterialExpressionWorldPosition);normal=node(unreal.MaterialExpressionVertexNormalWS)
        scale=node(unreal.MaterialExpressionScalarParameter);scale.set_editor_property('parameter_name','PhysicalWidthCM');scale.set_editor_property('default_value',float(item['physical_width_cm']))
        # Plank image's grooves run vertically in UV. Use world height for U on
        # vertical faces, with matching signed world-space normal basis.
        uvcode='float3 a=abs(N); if(a.z>max(a.x,a.y)) return float2(P.x,P.y*sign(N.z))/S; if(a.x>a.y) return float2(-P.z,P.y*sign(N.x))/S; return float2(-P.z,-P.x*sign(N.y))/S;'
        uv=custom(uvcode,{'P':world,'N':normal,'S':scale},unreal.CustomMaterialOutputType.CMOT_FLOAT2)
        samples={}
        for channel in ('Diffuse','nor_dx','arm'):
            n=node(unreal.MaterialExpressionTextureSampleParameter2D);n.set_editor_property('texture',textures[channel]);n.set_editor_property('parameter_name',channel)
            if channel=='nor_dx':n.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
            elif channel=='arm':n.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
            link(uv,'',n,'UVs');samples[channel]=n
        color=node(unreal.MaterialExpressionMultiply);factor=node(unreal.MaterialExpressionVectorParameter);factor.set_editor_property('parameter_name','ArtTint');factor.set_editor_property('default_value',unreal.LinearColor(*tint));link(samples['Diffuse'],'RGB',color,'A');link(factor,'',color,'B')
        output(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
        ncode='float3 n=normalize(N),a=abs(n); float3 u0=a.z>max(a.x,a.y)?float3(1,0,0):float3(0,0,-1); float3 u=normalize(u0-dot(u0,n)*n); float3 v=normalize(cross(n,u)); return normalize(T.x*u+T.y*v+T.z*n);'
        n=custom(ncode,{'T':samples['nor_dx'],'N':normal},unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        output(n,'',unreal.MaterialProperty.MP_NORMAL)
        for channel,prop in [('R',unreal.MaterialProperty.MP_AMBIENT_OCCLUSION),('G',unreal.MaterialProperty.MP_ROUGHNESS),('B',unreal.MaterialProperty.MP_METALLIC)]:output(samples['arm'],channel,prop)
        mat.set_editor_property('tangent_space_normal',False);lib.set_material_usage(mat,unreal.MaterialUsage.MATUSAGE_NANITE);lib.recompile_material(mat);error=unreal.EmeraldAuthoringLibrary.compile_material(mat)
        if error:raise RuntimeError('Quality material compilation failed: '+error)
        assets.save_loaded_asset(mat,only_if_is_dirty=False);palette[key]=mat
        report[key]={'asset':target,'source':item['source'],'physical_width_cm':item['physical_width_cm'],'channels':['Diffuse','nor_dx','arm'],'world_normal_basis':'Signed height-oriented planar projection','art_tint':tint}
    return report
