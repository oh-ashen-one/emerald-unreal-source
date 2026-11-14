#!/usr/bin/env python3
"""Make labeled source metatile contact sheets for authoring the visual mapping."""
from pathlib import Path
import json
from PIL import Image, ImageDraw
from import_littleroot import render_references, ROOT

if __name__ == '__main__':
    data=json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/littleroot.json').read_text())
    output=ROOT/'out/metatile-audit'
    output.mkdir(parents=True,exist_ok=True)
    for m in data['maps']:
        g=m['geometry']; unique={c['metatile_id']:c for c in g['cells']}
        cells=[]
        for i,(_,c) in enumerate(sorted(unique.items())):
            cells.append({**c,'x':i%8,'y':i//8})
        atlas={**g,'width':8,'height':(len(cells)+7)//8,'cells':cells}
        render_references(ROOT/'pokeemerald',{'maps':[{'geometry':atlas}],'layout_variants':[], 'tilesets':data['tilesets']},output)
        raw=Image.open(output/(m['name']+'.png'))
        labeled=Image.new('RGB',(8*90,atlas['height']*100),(22,25,29))
        draw=ImageDraw.Draw(labeled)
        for i,c in enumerate(cells):
            x,y=i%8,i//8
            labeled.paste(raw.crop((x*16,y*16,x*16+16,y*16+16)).resize((64,64),Image.Resampling.NEAREST),(x*90+13,y*100+4))
            draw.text((x*90+13,y*100+72),f"{c['metatile_id']:03X} c{c['collision']}",fill='white')
        labeled.save(output/(m['name']+'-labeled.png'))
        print(m['name'])
        for y in range(g['height']):
            print(' '.join(f"{c['metatile_id']:03X}" for c in g['cells'][y*g['width']:(y+1)*g['width']]))
