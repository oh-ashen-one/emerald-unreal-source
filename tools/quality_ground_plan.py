"""Visual wear/flowerbed plan from source walkability; no gameplay edits."""
from collections import deque
import json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def build(map_data):
    cells={(c['x'],c['y']):c for c in map_data['geometry']['cells']}
    allowed={p for p,c in cells.items() if not c['collision'] and c['metatile_id'] in (1,0x201) and c['elevation'] in (0,3,15)}
    hub=(10,12);ends=[(w['x'],w['y']+1) for w in map_data['warp_events']]+[(10,1)];segments=[];routes=[]
    for start in ends:
        if start not in allowed or hub not in allowed:raise ValueError('Source wear-path endpoint not ordinary walkable grass/doorstep')
        parent={start:None};pending=deque([start])
        while pending and hub not in parent:
            x,y=pending.popleft()
            for dx,dy in ((0,1),(1,0),(-1,0),(0,-1)):
                nxt=x+dx,y+dy
                if nxt in allowed and nxt not in parent:parent[nxt]=(x,y);pending.append(nxt)
        if hub not in parent:raise ValueError('No source-walkable visual route')
        path=[];p=hub
        while p is not None:path.append(p);p=parent[p]
        path.reverse();simple=[path[0]]
        for i in range(1,len(path)-1):
            previous=path[i][0]-path[i-1][0],path[i][1]-path[i-1][1];following=path[i+1][0]-path[i][0],path[i+1][1]-path[i][1]
            if previous!=following:simple.append(path[i])
        simple.append(path[-1]);routes.append({'start':list(start),'end':list(hub),'cells':[list(p) for p in path]})
        for a,b in zip(simple,simple[1:]):
            key=tuple(sorted((a,b)))
            if key not in segments:segments.append(key)
    return {'source_map':map_data['id'],'usage':'Visual ground wear only; collision/warp/event data unchanged','routes':routes,'segments_cm':[[a[0]*200,a[1]*200,b[0]*200,b[1]*200] for a,b in segments],'flower_centers_cm':[[p[0]*200,p[1]*200] for p,c in cells.items() if c['metatile_id']==4],'source_bounds_cm':[-100,-100,3900,3900],'path_inner_radius_cm':45,'path_outer_radius_cm':90}


def distance(plan,x,y):
    best=float('inf')
    for ax,ay,bx,by in plan['segments_cm']:
        dx,dy=bx-ax,by-ay;t=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy)));best=min(best,math.hypot(x-ax-t*dx,y-ay-t*dy))
    return best


def shader_mask(plan):
    code=['float d=100000;']
    for ax,ay,bx,by in plan['segments_cm']:
        code.append('{float2 a=float2(%s,%s),b=float2(%s,%s),v=b-a; float t=saturate(dot(P.xy-a,v)/dot(v,v)); d=min(d,length(P.xy-a-t*v));}'%(ax,ay,bx,by))
    code.append('float m=1-smoothstep(45,90,d*(1+.09*sin(P.x*.031)*sin(P.y*.023)));')
    for x,y in plan['flower_centers_cm']:code.append('m=max(m,1-smoothstep(65,98,length(P.xy-float2(%s,%s))));'%(x,y))
    flowers=plan['flower_centers_cm']
    for i,(ax,ay) in enumerate(flowers):
        for bx,by in flowers[i+1:]:
            if math.hypot(bx-ax,by-ay)>285:continue
            code.append('{float2 a=float2(%s,%s),b=float2(%s,%s),v=b-a;float t=saturate(dot(P.xy-a,v)/dot(v,v));m=max(m,1-smoothstep(65,98,length(P.xy-a-t*v)));}'%(ax,ay,bx,by))
    code.append('float inside=step(-100,P.x)*step(P.x,3900)*step(-100,P.y)*step(P.y,3900);return saturate(m*inside);')
    return ''.join(code)

if __name__=='__main__':
    data=json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/littleroot.json').read_text());m=next(m for m in data['maps'] if m['id']=='MAP_LITTLEROOT_TOWN');plan=build(m);(ROOT/'data/quality-ground-plan.json').write_text(json.dumps(plan,indent=2)+'\n');print('Source-connected visual routes',len(plan['routes']),'segments',len(plan['segments_cm']),'flowerbed centers',len(plan['flower_centers_cm']))
