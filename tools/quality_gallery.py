#!/usr/bin/env python3
"""Local-only matched screenshot review for the recording and art pass."""
import argparse,json,html
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from functools import partial
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--serve',action='store_true');args=parser.parse_args()
base=ROOT/'out/quality-pass';report=json.loads((ROOT/'data/native-quality-after-report.json').read_text());before=Path(report['before_run']).relative_to('out/quality-pass');after=Path(report['run']).relative_to('out/quality-pass')
views=[('TownOverhead.png','Town overhead'),('TownThirdPerson.png','Town third person'),('LittlerootTown_BrendansHouse_1F.png',"Brendan’s house · first floor"),('LittlerootTown_BrendansHouse_2F.png',"Brendan’s house · bedroom"),('LittlerootTown_MaysHouse_1F.png',"May’s house · first floor"),('LittlerootTown_MaysHouse_2F.png',"May’s house · bedroom"),('LittlerootTown_ProfessorBirchsLab.png',"Birch’s lab")]
for file,_ in views:
    for folder in (before,after):
        if not (base/folder/'shots'/file).is_file():raise SystemExit('Matched screenshot missing; gallery not written')
records={f:{'before':str(before/'shots'/f),'after':str(after/'shots'/f),'before_caption':'Before quality pass'} for f,_ in views}
perspective_path=ROOT/'data/native-perspective-after-report.json'
if perspective_path.exists():
    perspective=json.loads(perspective_path.read_text())
    if perspective.get('inspection_complete'):
        old=Path(perspective['before_run']).relative_to('out/quality-pass');current=Path(perspective['run']).relative_to('out/quality-pass')
        extra=[('Perspective_LittlerootTown.png','Town center path · third person'),('Perspective_LittlerootTown_BrendansHouse_1F.png','Brendan’s first floor · third person'),('Perspective_LittlerootTown_BrendansHouse_2F.png','Brendan’s bedroom · third person'),('Perspective_LittlerootTown_MaysHouse_1F.png','May’s first floor · third person'),('Perspective_LittlerootTown_MaysHouse_2F.png','May’s bedroom · third person'),('Perspective_LittlerootTown_ProfessorBirchsLab.png','Birch’s lab · third person')]
        for file,title in extra:
            for folder in (old,current):
                if not (base/folder/'shots'/file).is_file():raise SystemExit('Inspected perspective comparison missing')
            views.append((file,title));records[file]={'before':str(old/'shots'/file),'after':str(current/'shots'/file),'before_caption':'Before room pass'}
options=''.join('<option value="'+html.escape(f)+'">'+html.escape(title)+'</option>' for f,title in views)
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Littleroot quality pass</title><style>
*{box-sizing:border-box}body{margin:0;background:#101614;color:#e5efe9;font:16px system-ui,sans-serif}header{display:flex;align-items:center;gap:22px;padding:24px 32px;flex-wrap:wrap}h1{font-size:24px;margin:0;font-weight:620}select{font:inherit;padding:10px;color:inherit;background:#26372e;border:1px solid #678371;border-radius:6px}.status{margin-left:auto;color:#f2cf8d}main{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:0 24px}figure{margin:0;min-width:0}figcaption{padding:10px 0;color:#afc3b8}img{width:100%;height:auto;display:block;border:1px solid #405448;background:#000}footer{padding:24px 32px;line-height:1.6;color:#afc3b8}a{color:#b4e8ca}button{font:inherit;background:#26372e;border:1px solid #678371;color:inherit;padding:10px;border-radius:6px;cursor:pointer}body.single main{grid-template-columns:1fr}body.single figure:first-child{display:none}@media(max-width:800px){main{grid-template-columns:1fr}header{padding:18px}.status{margin-left:0}}
</style><header><h1>Littleroot quality pass</h1><select id="view" aria-label="View">OPTIONS</select><button id="focus">Enlarge current</button><span class="status">Quality gate open</span></header><main><figure><figcaption id="before-caption">Before quality pass</figcaption><img id="before" alt="Earlier actual Unreal render"></figure><figure><figcaption>Current</figcaption><img id="after" alt="Current actual Unreal render"></figure></main><footer>Matched actual Unreal views. Characters, fixtures, lighting and full gameplay remain under development. <a href="ASSETS.md">Asset credits</a></footer><script>
const records=FOLDERS;function update(){const row=records[document.getElementById('view').value];for(const name of ['before','after'])document.getElementById(name).src=row[name];document.getElementById('before-caption').textContent=row.before_caption;}document.getElementById('view').addEventListener('change',update);document.getElementById('focus').addEventListener('click',()=>{document.body.classList.toggle('single');document.getElementById('focus').textContent=document.body.classList.contains('single')?'Show comparison':'Enlarge current';});update();
</script></html>'''.replace('OPTIONS',options).replace('FOLDERS',json.dumps(records))
(base/'index.html').write_text(page);print('Wrote matched quality gallery',flush=True)
if args.serve:
    handler=partial(SimpleHTTPRequestHandler,directory=str(base));server=ThreadingHTTPServer(('127.0.0.1',0),handler)
    (base/'gallery-server.json').write_text(json.dumps({'port':server.server_port,'host':'127.0.0.1','scope':'Only out/quality-pass; task-owned review server'},indent=2)+'\n')
    print('Review at http://127.0.0.1:'+str(server.server_port),flush=True);server.serve_forever()
