#!/usr/bin/env python3
"""Code-built terrain adapter around the unmodified square source grid.

Ashen explicitly permits self-made assets for the November 13 quality pass.
The playable grid stays flat and authoritative; this noncolliding contextual
surface preserves its exact outer seam. Generated geometry is not source game art.
"""
import json
import math
from pathlib import Path
import struct
ROOT=Path(__file__).resolve().parents[1]

def height(x,y):
    distance=max(abs(x)-2000,abs(y)-2000,0)
    t=min(distance/1800,1);ramp=t*t*(3-2*t)
    return ramp*(350+170*math.sin(x/1700)*math.cos(y/2100)+80*math.sin((x+y)/850))

def main():
    step=200;radius=14000;n=radius*2//step+1;positions=[];normals=[];uvs=[];indices=[]
    for row in range(n):
        y=-radius+row*step
        for col in range(n):
            x=-radius+col*step;z=height(x,y);dx=(height(x+1,y)-height(x-1,y))/2;dy=(height(x,y+1)-height(x,y-1))/2
            length=math.sqrt(dx*dx+dy*dy+1)
            positions.extend((x/100,z/100,-y/100));normals.extend((-dx/length,1/length,dy/length));uvs.extend((x/200,y/200))
    for row in range(n-1):
        y=-radius+(row+.5)*step
        for col in range(n-1):
            x=-radius+(col+.5)*step
            if abs(x)<2000 and abs(y)<2000:continue
            a=row*n+col;b=a+1;c=a+n;d=c+1;indices.extend((a,b,c,b,d,c))
    blob=bytearray();views=[];accessors=[]
    def append(values,fmt,components,component_type,kind):
        while len(blob)%4:blob.append(0)
        start=len(blob);blob.extend(struct.pack('<'+fmt*len(values),*values));views.append({'buffer':0,'byteOffset':start,'byteLength':len(blob)-start})
        acc={'bufferView':len(views)-1,'componentType':component_type,'count':len(values)//components,'type':kind}
        if kind=='VEC3':acc.update(min=[min(values[i::3]) for i in range(3)],max=[max(values[i::3]) for i in range(3)])
        accessors.append(acc);return len(accessors)-1
    p=append(positions,'f',3,5126,'VEC3');no=append(normals,'f',3,5126,'VEC3');uv=append(uvs,'f',2,5126,'VEC2');ind=append(indices,'I',1,5125,'SCALAR')
    document={'asset':{'version':'2.0','generator':'Emerald source-grid terrain adapter'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'name':'SourceTerrain','mesh':0}],'meshes':[{'name':'SourceTerrain','primitives':[{'attributes':{'POSITION':p,'NORMAL':no,'TEXCOORD_0':uv},'indices':ind}]}],'buffers':[{'byteLength':len(blob)}],'bufferViews':views,'accessors':accessors}
    raw=json.dumps(document,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4);blob+=b'\0'*((-len(blob))%4)
    data=struct.pack('<III',0x46546c67,2,12+8+len(raw)+8+len(blob))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(blob),0x004e4942)+blob
    output=ROOT/'unreal/Emerald/Content/Imported/QualitySources/SourceTerrain.glb';output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(data)
    report={'source_grid_bounds_cm':[-100,-100,3900,3900],'ring_local_half_extent_cm':radius,'ring_hole_half_extent_cm':2000,'placement_cm':[1900,1900,0],'vertices':len(positions)//3,'triangles':len(indices)//3,'height_min_cm':min(positions[1::3])*100,'height_max_cm':max(positions[1::3])*100,'collision':'Disabled; original source grid unchanged','authorship':'Owner-authorized self-made terrain adapter, November13 quality gate; licensed scanned PBR applied separately'}
    (ROOT/'data/quality-terrain-plan.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
