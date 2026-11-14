#!/usr/bin/env python3
"""Original specimen analyzer geometry; no game artwork or meshes are inputs.

Source-first fit/rejection notes are recorded in LOG/ASSETS. Geometry is editable
through this generator; complete node scenes and licensed scan maps are retained.
"""
import hashlib,json,math,shutil,struct
from pathlib import Path
import numpy as np
from pack_static_gltf import pack
from bake_static_glb import bake
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'assets/source/original-lab-analyzer';BASE.mkdir(parents=True,exist_ok=True)
lock=json.loads((ROOT/'data/lab-metal-lock.json').read_text())
for f in lock['files']:
    source=ROOT/f['path'];raw=source.read_bytes()
    if len(raw)!=f['bytes'] or hashlib.sha256(raw).hexdigest()!=f['sha256']:raise SystemExit('Licensed lab metal differs')
    target=BASE/'textures'/source.name;target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists() and target.read_bytes()!=raw:raise SystemExit('Existing metal copy differs; preserved')
    if not target.exists():shutil.copyfile(source,target)

def scene(name):
    document={'asset':{'version':'2.0','generator':'Emerald original specimen analyzer/1'},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'bufferViews':[],'accessors':[],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}],'images':[{'name':Path(f['path']).stem,'uri':'textures/'+Path(f['path']).name} for f in lock['files']],'textures':[{'source':i,'sampler':0} for i in range(3)],'materials':[]}
    payload=bytearray();triangles=0
    for label,color,metal,rough,alpha in [('Steel',[.72,.78,.85],1,.8,1),('BluePaint',[.12,.48,.75],.18,1,1),('ViewingDome',[.12,.6,.78],0,.12,.32),('Rubber',[.025,.03,.035],0,1,1),('Display',[.02,.09,.12],0,.4,1),('StatusLight',[.2,.8,.8],0,.25,1)]:
        mat={'name':label,'pbrMetallicRoughness':{'baseColorTexture':{'index':0},'baseColorFactor':color+[alpha],'metallicRoughnessTexture':{'index':2},'metallicFactor':metal,'roughnessFactor':rough},'normalTexture':{'index':1,'scale':.08 if alpha<1 else .45},'occlusionTexture':{'index':2}}
        if alpha<1:mat.update(alphaMode='BLEND',doubleSided=True)
        if label in ('Display','StatusLight'):mat['emissiveFactor']=[.01,.12,.18] if label=='Display' else [.08,.7,.85]
        document['materials'].append(mat)
    def append(values,kind,component=5126):
        values=np.asarray(values,dtype='<f4' if component==5126 else '<u4');payload.extend(b'\0'*((-len(payload))%4));offset=len(payload);raw=values.tobytes();payload.extend(raw);view=len(document['bufferViews']);document['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(raw)})
        entry={'bufferView':view,'componentType':component,'count':len(values),'type':kind}
        if kind in ('VEC3','SCALAR'):entry.update(min=values.min(axis=0).tolist(),max=values.max(axis=0).tolist())
        document['accessors'].append(entry);return len(document['accessors'])-1
    def mesh(label,positions,normals,uv,indices,material):
        nonlocal triangles
        p=np.asarray(positions);n=np.asarray(normals);p=p[:,[0,2,1]];p[:,2]*=-1;n=n[:,[0,2,1]];n[:,2]*=-1
        if not np.isfinite(p).all() or not np.isfinite(n).all():raise ValueError('Nonfinite original geometry')
        primitive={'attributes':{'POSITION':append(p,'VEC3'),'NORMAL':append(n,'VEC3'),'TEXCOORD_0':append(uv,'VEC2')},'indices':append(np.asarray(indices).reshape(-1,1),'SCALAR',5125),'material':material}
        index=len(document['meshes']);document['meshes'].append({'name':label,'primitives':[primitive]});document['nodes'].append({'name':label,'mesh':index});document['scenes'][0]['nodes'].append(index);triangles+=len(indices)//3
    def lathe(label,profile,mat,center=(0,0,0),segments=96):
        positions=[];normals=[];uv=[];indices=[];length=0
        for (ra,za),(rb,zb) in zip(profile,profile[1:]):
            dr,dz=rb-ra,zb-za;l=math.hypot(dr,dz)
            if l<1e-9:continue
            start=len(positions)
            for radius,z,v in ((ra,za,length),(rb,zb,length+l)):
                for i in range(segments+1):
                    angle=i*math.tau/segments;c,s=math.cos(angle),math.sin(angle);positions.append([center[0]+radius*c,center[1]+radius*s,center[2]+z]);normals.append([dz/l*c,dz/l*s,-dr/l]);uv.append([i/segments*math.tau*max(ra,rb),v])
            for i in range(segments):
                a=start+i;b=a+1;d=a+segments+1;c=d+1
                if ra>1e-8:indices.extend([a,b,c])
                if rb>1e-8:indices.extend([a,c,d])
            length+=l
        mesh(label,positions,normals,uv,indices,mat)
    def rounded_box(label,center,size,radius,mat):
        h=np.asarray(size)/2;r=min(radius,float(min(h))*.95);inner=h-r;positions=[];normals=[];uv=[];indices=[]
        faces=[(0,1,1,1,2,1),(0,-1,1,-1,2,1),(1,1,0,-1,2,1),(1,-1,0,1,2,1),(2,1,0,1,1,1),(2,-1,0,-1,1,1)]
        for axis,sign,u,us,v,vs in faces:
            def coords(a):return [-h[a],-h[a]+r*.13,-h[a]+r*.5,-h[a]+r,0,h[a]-r,h[a]-r*.5,h[a]-r*.13,h[a]]
            cu,cv=coords(u),coords(v);start=len(positions)
            for y in cv:
                for x in cu:
                    p=np.zeros(3);p[axis]=sign*h[axis];p[u]=us*x;p[v]=vs*y;c=np.clip(p,-inner,inner);q=p-c;q/=np.linalg.norm(q);positions.append((c+q*r+center).tolist());normals.append(q.tolist());uv.append([x,y])
            for j in range(len(cv)-1):
                for i in range(len(cu)-1):
                    a=start+j*len(cu)+i;b=a+1;d=a+len(cu);c=d+1;indices.extend([a,b,c,a,c,d])
        mesh(label,positions,normals,uv,indices,mat)
    if name=='specimen_analyzer':
        lathe('BeveledBase',[(0,0),(1.43,0),(1.55,.05),(1.60,.13),(1.60,.20),(1.55,.25),(0,.25)],0)
        lathe('LowerGasket',[(0,.25),(1.46,.25),(1.48,.29),(1.48,.34),(1.44,.38),(0,.38)],3)
        lathe('BlueHousing',[(0,.35),(1.38,.35),(1.45,.41),(1.45,1.02),(1.38,1.09),(0,1.09)],1)
        lathe('InstrumentCollar',[(0,1.06),(1.42,1.06),(1.56,1.12),(1.56,1.20),(1.48,1.27),(1.16,1.27),(1.13,1.22),(0,1.22)],0)
        dome=[(1.15,1.23)]+[(1.15*math.cos(t),1.23+.65*math.sin(t)) for t in np.linspace(.02,math.pi/2,32)];lathe('BlueViewingDome',dome,2,segments=128)
        lathe('InternalSampleStage',[(0,1.22),(.85,1.22),(.88,1.26),(.85,1.30),(0,1.30)],0)
        for i in range(3):
            a=i*math.tau/3;x,y=.48*math.cos(a),.48*math.sin(a);lathe('SpecimenCanister_'+str(i),[(0,0),(.16,0),(.18,.03),(.18,.24),(.16,.27),(0,.27)],0,(x,y,1.30),32)
        for i in range(16):
            a=i*math.tau/16;x,y=1.36*math.cos(a),1.36*math.sin(a);lathe('CollarBolt_'+str(i),[(0,0),(.035,0),(.05,.015),(.05,.04),(.035,.055),(0,.055)],0,(x,y,1.27),16)
        for i in range(4):
            a=math.pi/4+i*math.pi/2;x,y=1.40*math.cos(a),1.40*math.sin(a);rounded_box('ReinforcingRib_'+str(i),np.array([x,y,.73]),[.17,.17,.69],.055,0)
        for i in range(12):
            a=i*math.tau/12;x,y=1.44*math.cos(a),1.44*math.sin(a);rounded_box('VentRecess_'+str(i),np.array([x,y,.58]),[.10,.10,.29],.025,3)
        rounded_box('FrontReadout',np.array([0,1.445,.89]),[.65,.08,.29],.035,4)
        for i in range(4):rounded_box('StatusSegment_'+str(i),np.array([-.20+i*.13,1.495,.89]),[.07,.02,.10],.009,5)
    else:
        rounded_box('ControllerCabinet',np.array([0,0,1.03]),[1.30,1.20,1.98],.10,1)
        rounded_box('TopTrim',np.array([0,0,2.04]),[1.34,1.24,.10],.035,0)
        rounded_box('FrontPanel',np.array([0,.605,1.42]),[1.08,.10,.81],.045,0)
        rounded_box('DisplayGlass',np.array([0,.665,1.50]),[.85,.035,.43],.015,4)
        for i in range(6):rounded_box('ReadoutBar_'+str(i),np.array([-.30+i*.12,.689,1.45]),[.055,.012,.10+.03*(i%3)],.004,5)
        for i in range(3):rounded_box('ControlKey_'+str(i),np.array([-.28+i*.28,.68,1.12]),[.15,.08,.10],.025,0)
        for i in range(8):rounded_box('FrontVent_'+str(i),np.array([0,.61,.40+i*.055]),[.76,.04,.025],.008,3)
        for x in (-.43,.43):
            for y in (-.39,.39):rounded_box('RubberFoot',np.array([x,y,.04]),[.20,.20,.08],.025,3)
    document['buffers']=[{'uri':name+'.bin','byteLength':len(payload)}];document['extras']={'authorship':'Original project specimen-analysis equipment, generated from editable code. No Nintendo artwork/meshes used. Licensed CC0 metal surface maps recorded separately.'}
    source=BASE/(name+'.gltf');source.write_text(json.dumps(document,separators=(',',':')));(BASE/(name+'.bin')).write_bytes(payload)
    packed=ROOT/'out/quality-pass/packed-original-lab'/(name+'.glb');pack(source,packed);target=ROOT/'unreal/Emerald/Content/Imported/SourceModels'/('Original_'+name+'.glb');result=bake(packed,target);result['triangles']=triangles
    return {'id':name,'name':name.replace('_',' ').title(),'author':'Original project geometry','url':'tools/build_original_lab_analyzer.py','license':'Original project geometry; CC0-1.0 surface maps','baked_file':str(target.relative_to(ROOT)),'baked':result,'texture_token':'metal_plate_02','source_files':[]}

assets=[scene(name) for name in ('specimen_analyzer','analyzer_controller')]
(ROOT/'data/original-lab-analyzer-report.json').write_text(json.dumps({'geometry_authoring':'tools/build_original_lab_analyzer.py','maps':'data/lab-metal-lock.json','assets':assets,'scope':'Original candidate geometry only; native import/render/footprint fit not yet verified','quality_gate_passed':False},indent=2)+'\n')
print('Generated original complete lab candidates:',[(a['id'],a['baked']['source_mesh_instances'],a['baked']['triangles']) for a in assets])
