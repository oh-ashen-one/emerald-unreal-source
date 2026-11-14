#!/usr/bin/env python3
"""Plan an input-only traversal covering all source warps for the UE smoke driver.

This uses source-grid movement plus source animated-door and arrow-warp rules.
It does not bypass collisions by teleporting, and does not assert story-state/NPC
semantics. The generated route is for a separate geometry/travel validation mode.
"""
from collections import deque
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def make_plan(data):
    maps={m['id']:m for m in data['maps']}
    def cell(mid,x,y):
        g=maps[mid]['geometry']
        return g['cells'][y*g['width']+x] if 0<=x<g['width'] and 0<=y<g['height'] else None
    def edge(state,dx,dy):
        mid,x,y=state
        current=cell(mid,x,y)
        c=cell(mid,x+dx,y+dy)
        if not c: return None
        possible_door=c['behavior_name']=='MB_ANIMATED_DOOR' and (dx,dy)==(0,-1)
        warps=maps[mid]['warp_events']
        wi=next((i for i,w in enumerate(warps) if (w['x'],w['y'])==(x+dx,y+dy)),None)
        if c['collision'] and not(possible_door and wi is not None): return None
        if current['elevation'] and c['elevation'] not in (0,15,current['elevation']): return None
        dest=(mid,x+dx,y+dy)
        via=None
        if wi is not None and not(c['behavior_name']=='MB_SOUTH_ARROW_WARP' and (dx,dy)!=(0,1)):
            warp=warps[wi]
            target=maps[warp['dest_map']]['warp_events'][int(warp['dest_warp_id'])]
            dest=(warp['dest_map'],target['x'],target['y'])
            arrival=cell(*dest)
            if arrival['behavior_name']=='MB_ANIMATED_DOOR':
                south=cell(dest[0],dest[1],dest[2]+1)
                if south and not south['collision']: dest=(dest[0],dest[1],dest[2]+1)
            via=(mid,wi)
        return dest,via
    state=('MAP_LITTLEROOT_TOWN',10,10)
    steps=[]
    covered=set()
    targets=[(m['id'],i) for m in data['maps'] for i in range(len(m['warp_events']))]
    for goal in targets:
        if goal in covered: continue
        queue=deque([(state,[])])
        seen={state}
        found=None
        while queue and found is None:
            here,path=queue.popleft()
            for dx,dy in [(0,-1),(-1,0),(1,0),(0,1)]:
                result=edge(here,dx,dy)
                if result is None: continue
                dest,via=result
                step={'from_map':here[0],'from_tile':list(here[1:]),'direction':[dx,dy],
                      'expect_map':dest[0],'expect_tile':list(dest[1:]),
                      'via_warp':{'map':via[0],'index':via[1]} if via else None}
                extended=path+[step]
                if via==goal:
                    found=(dest,extended)
                    break
                if dest not in seen:
                    seen.add(dest); queue.append((dest,extended))
        if found is None: raise RuntimeError('Warp unreachable by source-grid inputs: '+str(goal))
        state,path=found
        steps.extend(path)
        covered.update((s['via_warp']['map'],s['via_warp']['index']) for s in path if s['via_warp'])
    if len(covered)!=13: raise RuntimeError('Incomplete warp coverage')
    return {'schema':'emerald.traversal/1','source_revision':data['source_revision'],
            'start_map':'MAP_LITTLEROOT_TOWN','start_tile':[10,10],
            'scope':'geometry/travel mode; source story-state/NPC semantics not covered',
            'covered_warps':[{'map':m,'index':i} for m,i in sorted(covered)],'steps':steps}

if __name__=='__main__':
    path=ROOT/'unreal/Emerald/Content/Imported/Data'
    plan=make_plan(json.loads((path/'littleroot.json').read_text()))
    (path/'traversal.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(len(plan['steps']),'input steps;',len(plan['covered_warps']),'source warps covered in plan; runtime unverified')
