"""Embed selected local glTF buffers/images without changing its geometry.

Network acquisition is separate. Refuse URI schemes and path escapes; never
execute asset scripts. The existing static-scene baker handles all instances.
"""
import copy
import base64
import json
from pathlib import Path
import struct
from urllib.parse import unquote


def pack(source, destination):
    source=Path(source).resolve();base=source.parent
    doc=json.loads(source.read_text());binary=bytearray();offsets=[]
    def read(uri):
        if uri.startswith('data:'):
            header,encoded=uri.split(',',1)
            if header not in ('data:application/octet-stream;base64','data:application/gltf-buffer;base64','data:image/png;base64','data:image/jpeg;base64'):
                raise ValueError('Unsupported embedded dependency type')
            if len(encoded)>32*1024*1024:raise ValueError('Embedded dependency exceeds bound')
            return base64.b64decode(encoded,validate=True)
        uri=unquote(uri,errors='strict')
        if ':' in uri or '\\' in uri or '\0' in uri:raise ValueError('External URI scheme is not a local dependency')
        path=(base/uri).resolve()
        if not path.is_relative_to(base):raise ValueError('Dependency path escapes source directory')
        return path.read_bytes()
    def append(data):
        binary.extend(b'\0'*((-len(binary))%4));offset=len(binary);binary.extend(data);return offset
    for buffer in doc.get('buffers',[]):
        data=read(buffer['uri'])
        if len(data)!=buffer['byteLength']:raise ValueError('Buffer length mismatch')
        offsets.append(append(data))
    for view in doc.get('bufferViews',[]):
        original=copy.copy(view);i=original['buffer']
        if original.get('byteOffset',0)+original['byteLength']>doc['buffers'][i]['byteLength']:
            raise ValueError('Buffer view outside source buffer')
        view['byteOffset']=offsets[i]+original.get('byteOffset',0);view['buffer']=0
    for image in doc.get('images',[]):
        if 'uri' not in image:continue
        data=read(image.pop('uri'))
        mime='image/png' if data.startswith(b'\x89PNG\r\n\x1a\n') else ('image/jpeg' if data.startswith(b'\xff\xd8') else None)
        if not mime:raise ValueError('Unsupported image dependency')
        image['mimeType']=mime;image['bufferView']=len(doc.setdefault('bufferViews',[]))
        doc['bufferViews'].append({'buffer':0,'byteOffset':append(data),'byteLength':len(data)})
    doc['buffers']=[{'byteLength':len(binary)}]
    text=json.dumps(doc,separators=(',',':')).encode();text+=b' '*((-len(text))%4)
    binary.extend(b'\0'*((-len(binary))%4))
    data=struct.pack('<III',0x46546c67,2,28+len(text)+len(binary))
    data+=struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(binary),0x004e4942)+binary
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
    return len(data)
