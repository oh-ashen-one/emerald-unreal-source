#!/usr/bin/env python3
"""Sample original static reference swatches; lighting still changes rendered color."""
from collections import Counter
import json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

def swatch(name,box,predicate=lambda rgb:True):
    im=Image.open(ROOT/'out/source-reference'/(name+'.png')).convert('RGB')
    color=next(rgb for rgb,_ in Counter(im.crop(box).get_flattened_data()).most_common() if predicate(rgb))
    def linear(c):
        c=c/255
        return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
    return {'rgb8':list(color),'linear_rgba':[linear(c) for c in color]+[1],
            'reference':name,'sample_box_pixels':box}
if __name__=='__main__':
    result={
        'Rug':swatch('LittlerootTown_BrendansHouse_2F',[64,48,128,112]),
        'RugPink':swatch('LittlerootTown_MaysHouse_2F',[16,48,80,112]),
        'TablePink':swatch('LittlerootTown_BrendansHouse_1F',[48,96,80,128],lambda c:c[0]>c[1]+10 and c[2]>c[1]+10),
        'TableYellow':swatch('LittlerootTown_MaysHouse_1F',[96,96,128,128],lambda c:c[0]>c[2]+30 and c[1]>c[2]+30),
        'ChairGreen':swatch('LittlerootTown_BrendansHouse_1F',[32,96,48,112],lambda c:c[1]>c[0]+20 and c[1]>c[2]+20)}
    art=ROOT/'out/source-reference/art-samples';art.mkdir(parents=True,exist_ok=True)
    im=Image.open(ROOT/'out/source-reference/LittlerootTown_BrendansHouse_2F.png').convert('RGB')
    im.crop((33,11,47,19)).resize((512,512),Image.Resampling.NEAREST).save(art/'RegionPrint.png')
    lab=Image.open(ROOT/'out/source-reference/LittlerootTown_ProfessorBirchsLab.png').convert('RGB').crop((80,48,96,64))
    lab.resize((512,512),Image.Resampling.NEAREST).save(art/'LabFloorPattern.png')
    lab.convert('L').resize((512,512),Image.Resampling.NEAREST).save(art/'LabFloorHeight.png')
    (ROOT/'data/source-style.json').write_text(json.dumps(result,indent=2)+'\n')
    print({k:v['rgb8'] for k,v in result.items()})
