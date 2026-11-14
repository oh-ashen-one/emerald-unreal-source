"""Acquire only selected CC0 model dependencies, verified by pinned SHA-256."""
import hashlib
import json
from pathlib import Path
import urllib.request
from pack_static_gltf import pack

ROOT=Path(__file__).resolve().parents[1]


def acquire():
    lock=json.loads((ROOT/'data/prop-lock.json').read_text())
    for model in lock['models']:
        for item in model['files']:
            path=ROOT/item['path']
            if not path.exists():
                req=urllib.request.Request(item['url'],headers={'User-Agent':'EmeraldPrivateReconstruction/1.0'})
                with urllib.request.urlopen(req,timeout=60) as r:data=r.read(32*1024*1024+1)
                if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:
                    raise RuntimeError('Model dependency differs: '+path.name)
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
            if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
                raise RuntimeError('Existing model dependency differs; preserved: '+path.name)
        path=ROOT/model['packed_path'];pack(ROOT/model['gltf_path'],path)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=model['packed_sha256']:
            raise RuntimeError('Packed model changed: '+model['name'])
    print('Verified',len(lock['models']),'selected CC0 model assemblies and dependencies')


if __name__=='__main__':acquire()
