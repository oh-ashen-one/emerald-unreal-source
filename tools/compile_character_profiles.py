"""Compile role palette samples from the pinned original sprite PNGs."""
import json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'pokeemerald/graphics/object_events/pics/people'
# Each value is an actual original palette index, not a new painted skin.
SPECS={
 'mom':('Casual_Female','mom',{'Hair':4,'Main':8,'Black':5,'Brown':6}),
 'birch':('Doctor_Male_Young','prof_birch',{'Hair':12,'Main':14,'Black':8,'Brown':13}),
 'scientist':('Doctor_Male_Young','scientist_1',{'Hair':13,'Main':5,'Black':7,'Brown':13}),
 'twin':('Casual_Female','twin',{'Hair':12,'Main':5,'Black':8,'Brown':10}),
 'boy':('Casual_Male','boy_2',{'Hair':12,'Main':5,'Black':11,'Brown':13}),
 'fat_man':('Casual_Bald','fat_man',{'Main':8,'Black':11,'Brown':13}),
 'rival_mom':('Casual_Female','woman_4',{'Hair':12,'Main':5,'Black':7,'Brown':13}),
 'sibling':('Casual_Male','ninja_boy',{'Hair':12,'Main':5,'Black':11,'Brown':13}),
 'norman':('Casual_Male','gym_leaders/norman',{'Hair':7,'Main':11,'Black':6,'Brown':7}),
 'player_male':('Casual_Male','brendan/walking',{'Hair':4,'Main':7,'Black':12,'Brown':8}),
 'player_female':('Casual_Female','may/walking',{'Hair':7,'Main':12,'Black':6,'Brown':8})}
GRAPHICS={'MOM':'mom','PROF_BIRCH':'birch','SCIENTIST_1':'scientist','TWIN':'twin','BOY_2':'boy','FAT_MAN':'fat_man','WOMAN_4':'rival_mom','NINJA_BOY':'sibling','NORMAN':'norman','RIVAL_BRENDAN_NORMAL':'player_male','RIVAL_MAY_NORMAL':'player_female','BRENDAN_NORMAL':'player_male','MAY_NORMAL':'player_female'}
if __name__=='__main__':
 constants=json.loads((ROOT/'unreal/Emerald/Content/Imported/Data/source-events.json').read_text())['constants'];profiles={}
 for key,(model,source,indices) in SPECS.items():
  path=SOURCE/(source+'.png');im=Image.open(path);palette=im.getpalette();indices={**indices,'Skin':2,'Face':15};pixels=list(im.crop((0,0,16,im.height)).get_flattened_data());ys=[i//16 for i,p in enumerate(pixels) if p!=0];height=max(ys)-min(ys)+1
  profiles[key]={'model':model,'source_sprite':str(path.relative_to(ROOT)),'height_cm':300.*height/20.,'width_scale':1.2 if key=='fat_man' else 1.,'forward_yaw':0.,'palette_indices':indices,'colors_rgb8':{n:palette[i*3:i*3+3] for n,i in indices.items()},'source_visible_height_px':height}
 result={'schema':'emerald.character-profiles/1','profiles':profiles,'graphics':{str(constants['OBJ_EVENT_GFX_'+name]):role for name,role in GRAPHICS.items()},'players':{'male':'player_male','female':'player_female'},'scope':'Licensed staging silhouettes with original palette/height anchors; caps/dresses/hair/likeness still require refinement'}
 (ROOT/'data/character-role-plan.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Compiled',len(profiles),'source palette/height roles')
