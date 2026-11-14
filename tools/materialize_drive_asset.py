"""Materialize an authenticated connector file reference supplied on stdin.

Never log or persist its temporary signed URL. Model provenance uses canonical
Drive IDs/URLs and hashes instead. This helper does not acquire credentials.
"""
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]


def main():
    spec=json.loads(sys.stdin.readline())
    name=spec['name']
    if not re.fullmatch(r'[A-Za-z0-9_.-]+',name):raise ValueError('Invalid asset filename')
    parsed=urllib.parse.urlparse(spec['url'])
    if parsed.scheme!='https' or not (parsed.hostname or '').endswith('.oaiusercontent.com'):
        raise ValueError('Expected connector file reference')
    request=urllib.request.Request(spec['url'],headers={'User-Agent':'EmeraldPrivateReconstruction/1.0'})
    with urllib.request.urlopen(request,timeout=60) as response:
        data=response.read(16*1024*1024+1)
    if len(data)!=spec['bytes'] or len(data)>16*1024*1024:raise ValueError('Asset length mismatch')
    output=ROOT/'assets/source/quaternius-characters'/name
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists() and output.read_bytes()!=data:raise ValueError('Existing source differs; preserved')
    output.write_bytes(data)
    print(json.dumps({'path':str(output.relative_to(ROOT)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}))


if __name__=='__main__':
    try:main()
    except Exception as error:
        # A provider exception may contain its URL. Report only the type/code.
        print('Asset materialization failed:',type(error).__name__,getattr(error,'code',''),file=sys.stderr)
        sys.exit(1)
