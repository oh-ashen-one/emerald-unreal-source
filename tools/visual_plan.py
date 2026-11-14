"""Compile house furnishing anchors/compound coverage directly from source cells.

Drawing heights and margins are art parameters; floor centers/footprints are
source-grid derived. Unrecognized blocked cells remain explicit diagnostics.
"""
from collections import Counter

TILE=200


def house_plan(m):
    g=m['geometry']; cells={(c['x'],c['y']):c for c in g['cells']}
    objects=[]; covered={}; bedroom=m['name'].endswith('_2F')
    wall_ids={0x208,0x209,0x20A,0x20B,0x20C,0x20D,0x20F,0x213,0x215,
              0x210,0x212,0x216,0x217,0x21E,0x21F,0x226,0x227,0x24D,0x251,
              0x252,0x254,0x256,0x26D,0x26E,0x26F,0x275,0x276,0x277}

    def add(asset,anchor,size,offset=(0,0,0),yaw=0,parts=None,material=None,kind=None):
        x,y=anchor; source=cells[(x,y)]
        object_id=f"{kind or asset}_{x}_{y}"
        claimed=[]
        for dx,dy,expected in parts or [(0,0,source['metatile_id'])]:
            coord=(x+dx,y+dy)
            if coord not in cells or cells[coord]['metatile_id']!=expected:
                raise ValueError(f"{m['name']}: changed source compound {object_id} at {coord}")
            claimed.append(list(coord))
            if cells[coord]['collision']:
                prior=covered.get(coord)
                if prior and prior!=object_id: raise ValueError('Conflicting compound coverage '+str(coord))
                covered[coord]=object_id
        objects.append({'id':object_id,'asset':asset,'source_anchor':[x,y],
                        'source_metatile':source['metatile_id'],'source_cells':claimed,
                        'center_cm':[x*TILE+offset[0],y*TILE+offset[1],offset[2]],
                        'size_cm':list(size),'yaw':yaw,'material':material})
        return objects[-1]

    def detail(asset,parent,size,offset,yaw=0):
        x,y=parent['source_anchor']
        objects.append({'id':parent['id']+'_'+asset,'asset':asset,'source_anchor':[x,y],
                        'source_metatile':parent['source_metatile'],'source_cells':[],
                        'center_cm':[x*TILE+offset[0],y*TILE+offset[1],offset[2]],
                        'size_cm':list(size),'yaw':yaw,'material':None,'parent':parent['id']})

    for (x,y),c in cells.items():
        mid=c['metatile_id']; anchor=(x,y)
        if c['behavior_name']=='MB_TELEVISION':
            add('televisionVintage',anchor,(175,130,160),kind='SourceTV')
        if bedroom and mid in (0x265,0x257):
            add('gamingConsole',anchor,(160,145,50),parts=[(0,-1,0x254),(0,0,mid)],kind='SourceGameConsole')
        if mid in (0x25A,0x259) and bedroom:
            pc=add('kitchenCabinet',anchor,(180,150,105),kind='SourcePC')
            detail('computerTerminal',pc,(135,120,125),(0,15,105))
        if bedroom and mid in (0x284,0x289):
            add('bedSingle',anchor,(175,360,145),(0,100,0),parts=[(0,0,mid),(0,1,0x28C if mid==0x284 else 0x291)],kind='SourceBed')
        if bedroom and mid in (0x298,0x29B):
            # Four by four source decoration/rug cells, not an offset single tile.
            for dy in range(4):
                for dx in range(4):
                    if not cells[(x+dx,y+dy)]['behavior_name'].startswith('MB_HOLDS_'):
                        raise ValueError('Changed rug footprint')
            add('rugSquare',anchor,(780,780,3),(300,300,1),material='RugPink' if 'Mays' in m['name'] else 'Rug',kind='SourceRug')
        if not bedroom:
            if mid==0x238:
                add('kitchenFridgeSmall',anchor,(180,175,270),parts=[(0,0,0x238),(0,-1,0x230)],kind='SourceFridge')
            if mid==0x239:
                add('kitchenSink',anchor,(180,175,135),parts=[(0,0,0x239),(0,-1,0x231)],kind='SourceSink')
            if mid==0x23A:
                add('kitchenStoveElectric',anchor,(180,175,135),parts=[(0,0,0x23A),(0,-1,0x232)],kind='SourceStove')
            if mid in (0x23B,0x24B):
                pattern=[(0,0,mid),(1,0,0x23C if mid==0x23B else 0x24C),
                         (0,-1,0x233 if mid==0x23B else 0x243),(1,-1,0x234 if mid==0x23B else 0x244)]
                add('bookcaseClosedWide',anchor,(370,145,270),(100,0,0),parts=pattern,kind='SourceKitchenCupboard')
            if mid in (0x21A,0x2B9):
                pattern=[(0,0,mid),(1,0,0x21B if mid==0x21A else 0x2BA),
                         (0,1,0x222 if mid==0x21A else 0x2C1),(1,1,0x223 if mid==0x21A else 0x2C2)]
                add('tableCrossCloth',anchor,(360,360,130),(100,100,0),parts=pattern,kind='SourceDiningTable')
            if mid in (0x219,0x221,0x2C0):
                add('chairModernCushion',anchor,(110,130,150),yaw=90,kind='SourceDiningChair')
            if mid in (0x21C,0x224,0x2C3):
                add('chairModernCushion',anchor,(110,130,150),yaw=-90,kind='SourceDiningChair')
            if mid==0x240:
                add('tableCoffee',anchor,(370,150,95),(100,0,0),parts=[(0,0,0x240),(1,0,0x241)],kind='SourceLivingTable')
            if mid in (0x235,0x2B0):
                # Six by four source carpet area; under-table cells remain owned by the table.
                add('rugSquare',anchor,(1180,780,3),(500,300,1),material='RugPink' if 'Mays' in m['name'] else 'Rug',kind='SourceDiningRug')

    if bedroom:
        for event in m['bg_events']:
            if event['script'].endswith('_Notebook'):
                parent=add('table',(event['x'],event['y']),(180,155,110),kind='SourceNotebookDesk')
                detail('books',parent,(110,85,14),(0,0,110))

    if bedroom:
        for event in m['bg_events']:
            if event['script'].endswith('_WallClock'):
                x,y=event['x'],event['y']
                add('wallClock',(x,y),(150,35,150),(0,-215,190),yaw=0,
                    parts=[(0,-1,0x227 if 'Mays' in m['name'] else 0x287),
                           (0,0,0x22F if 'Mays' in m['name'] else 0x28F)],kind='SourceWallClock')
        for (x,y),c in cells.items():
            if c['metatile_id']==0x255:
                add('regionMapFrame',(x,y),(175,20,110),(0,-215,215),yaw=0,
                    parts=[(0,-1,0x250),(0,0,0x255)],kind='SourceRegionMap')

    # One room shell represents the source background wall projection, rather
    # than turning its two sprite rows into repeated physical wall rows.
    wall_cells=[]
    for coord,c in cells.items():
        if c['collision'] and coord not in covered and (c['y']==0 or c['metatile_id'] in wall_ids):
            covered[coord]='SourceWallProjection';wall_cells.append(list(coord))
    for e in m['warp_events']:
        c=cells[(e['x'],e['y'])]
        if c['behavior_name']=='MB_NON_ANIMATED_DOOR':
            add('stairs',(e['x'],e['y']),(175,210,235),kind='SourceStairs')
    diagnostics=[{'xy':list(p),'metatile_id':c['metatile_id']} for p,c in cells.items()
                 if c['collision'] and p not in covered]
    return {'map':m['id'],'objects':objects,'wall_projection_cells':wall_cells,
            'blocked_coverage':[{'xy':list(p),'object':owner} for p,owner in sorted(covered.items())],
            'diagnostics':diagnostics,'physical_back_wall_y_cm':-70,
            'stair_frames':[{'xy':[e['x'],e['y']],'posts':[[e['x']+dx,e['y']] for dx in (-1,1) if cells.get((e['x']+dx,e['y']),{}).get('collision')]} for e in m['warp_events'] if cells[(e['x'],e['y'])]['behavior_name']=='MB_NON_ANIMATED_DOOR'],
            'scope':'Source furniture and wall projection; story/NPC/decorative detail still incomplete'}


def lab_plan(m):
    """Original lab compounds, including projection cells and BG anchors.

    Source sprite rows can project above a fixture's floor contact. Only the
    explicit blocked coverage changes classification; runtime collision is raw.
    The original replacement analyzer retains the machine's exact source cells.
    """
    cells={(c['x'],c['y']):c for c in m['geometry']['cells']}
    objects=[];covered={}
    def add(kind,asset,anchor,size,center,parts,yaw=0,material=None):
        identifier=f'{kind}_{anchor[0]}_{anchor[1]}'
        claimed=[]
        for x,y,expected in parts:
            if cells[x,y]['metatile_id']!=expected:
                raise ValueError(f"{m['name']}: changed source compound {identifier} at {(x,y)}")
            claimed.append([x,y])
            if cells[x,y]['collision']:
                if (x,y) in covered:raise ValueError('Conflicting lab coverage')
                covered[x,y]=identifier
        item={'id':identifier,'asset':asset,'source_anchor':list(anchor),
              'source_metatile':cells[anchor]['metatile_id'],'source_cells':claimed,
              'center_cm':list(center),'size_cm':list(size),'yaw':yaw,'material':material}
        objects.append(item);return item
    def detail(kind,asset,parent,size,center,yaw=0,material=None):
        item=add(kind,asset,tuple(parent['source_anchor']),size,center,[],yaw,material)
        item['parent']=parent['id'];return item
    # North shelves: top two sprite rows are not two physical bookshelves.
    shelf=add('SourceLabBookshelf','bookcaseClosedWide',(0,1),(370,145,275),(100,220,0),
              [(0,0,0x210),(1,0,0x211),(0,1,0x218),(1,1,0x219),(0,2,0x220),(1,2,0x221)])
    shelves=[shelf]
    for x in (0,2):
        shelf=add('SourceLabBookshelf','bookcaseClosedWide',(x,7),(370,145,275),(x*200+100,1400,0),
                  [(x,6,0x22C),(x+1,6,0x22D),(x,7,0x234),(x+1,7,0x235)])
        shelves.append(shelf)
        add('SourceShelfBox','cardboardBoxClosed',(x,5),(150,130,140),(x*200+100,1400,275),
            [(x,5,0x224 if x==0 else 0x236),(x+1,5,0x225 if x==0 else 0x237)])
    for shelf in shelves:
        x,y,_=shelf['center_cm']
        for level in range(3):
            detail(f'SourceShelfBooks{level}','books',shelf,(300,75,62),(x,y+24,38+level*83))
    # Original PC counter at (3..4,1), and the book counter at (6..9,1).
    top=add('SourceLabPCDesk','desk',(3,1),(370,165,115),(700,200,0),
            [(3,0,0x212),(4,0,0x213),(3,1,0x21A),(4,1,0x21B),(3,2,0x222),(4,2,0x223)])
    detail('SourceLabTerminal','computerTerminal',top,(135,125,135),(790,205,115))
    counter=add('SourceBookCounter','desk',(6,1),(770,170,115),(1500,200,0),
                [(6,1,0x20B),(7,1,0x20C),(8,1,0x20D),(9,1,0x20E)])
    for x in (7,8,9):detail(f'SourceCounterBooks{x}','books',counter,(120,90,28),(x*200,200,115))
    for x,y,mid,height in [(11,2,0x29A,135),(12,2,0x29A,135),(12,3,0x232,135),
                           (0,10,0x248,135),(0,11,0x248,135)]:
        add('SourceFloorBooks','books',(x,y),(155,130,height),(x*200,y*200,0),[(x,y,mid)])
    for x,y,mid,height in [(0,3,0x228,150),(9,4,0x231,150),(10,4,0x242,290),(12,11,0x242,290)]:
        add('SourceLabBox','cardboardBoxClosed',(x,y),(165,165,height),(x*200,y*200,0),[(x,y,mid)])
    # Mirrored side PCs: desks and screens face the source green chairs.
    for x,chairx,yaw,mids in [(1,2,-90,(0x230,0x238,0x240)),(11,10,90,(0x23B,0x243,0x24B))]:
        desk=add('SourceSidePCDesk','desk',(x,10),(370,170,115),(x*200,2000,0),
                 [(x,9,mids[0]),(x,10,mids[1]),(x,11,mids[2])],yaw)
        away=-1 if x==1 else 1
        detail('SourceSideTerminal','computerTerminal',desk,(135,125,135),(x*200+away*45,2000,115),yaw)
        detail('SourceSideChair','chairModernCushion',desk,(110,125,150),(chairx*200,2000,0),-yaw)
    add('SourceLabChair','chairModernCushion',(4,3),(110,125,150),(800,600,0),[(4,3,0x241)],180)
    for x,y,parts in [(2,2,[(2,1,0x23C),(2,2,0x244)]),(12,9,[(12,9,0x22E)]),(3,12,[(3,11,0x226),(3,12,0x22E)])]:
        add('SourceLabPlant','plantSmall1',(x,y),(150,150,230),(x*200,y*200,0),parts)
    add('SourceLabAnalyzer','specimenAnalyzer',(10,7),(350,350,220),(2100,1300,0),
        [(10,6,0x214),(11,6,0x215),(10,7,0x21C),(11,7,0x21D)])
    add('SourceAnalyzerController','analyzerController',(12,7),(145,145,210),(2400,1400,0),[(12,7,0x21E)])
    wall=[]
    for xy,c in cells.items():
        if c['collision'] and xy not in covered and (c['y']==0 or c['metatile_id']==0x20A):
            covered[xy]='SourceWallProjection';wall.append(list(xy))
    diagnostics=[{'xy':list(xy),'metatile_id':c['metatile_id']} for xy,c in cells.items()
                 if c['collision'] and xy not in covered]
    return {'map':m['id'],'objects':objects,'wall_projection_cells':wall,
            'blocked_coverage':[{'xy':list(xy),'object':owner} for xy,owner in sorted(covered.items())],
            'diagnostics':diagnostics,'physical_back_wall_y_cm':-70,'stair_frames':[],
            'scope':'All source lab compounds represented; original analyzer replaces machine footprint; story layout changes not rendered'}


def compile_plans(data):
    plans={m['name']:house_plan(m) for m in data['maps'] if 'House' in m['name']}
    return {'schema':'emerald.visual-plan/3','source_revision':data['source_revision'],'houses':plans,
            'labs':{m['name']:lab_plan(m) for m in data['maps'] if 'ProfessorBirchsLab' in m['name']}}

if __name__=='__main__':
    import json
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    path=root/'unreal/Emerald/Content/Imported/Data'
    p=compile_plans(json.loads((path/'littleroot.json').read_text()))
    (path/'visual-plan.json').write_text(json.dumps(p,indent=2)+'\n')
    for name,plan in p['houses'].items():
        print(name,Counter(x['asset'] for x in plan['objects']),len(plan['diagnostics']),'explicit unmapped blocked cells')
