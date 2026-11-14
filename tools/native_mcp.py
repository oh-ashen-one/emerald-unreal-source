#!/usr/bin/env python3
"""Thin JSON-RPC client for Epic's native loopback MCP; no replacement bridge."""
import json
import os
import sys
import subprocess
from pathlib import Path
import urllib.request
from urllib.parse import urlparse

class NativeMCP:
    def __init__(self,url=None):
        self.url=url or os.environ.get('EMERALD_MCP_URL','http://127.0.0.1:'+os.environ.get('EMERALD_MCP_PORT','8876')+'/mcp')
        if urlparse(self.url).hostname not in ('127.0.0.1','localhost','::1'):
            raise ValueError('This project client is loopback only')
        self.verify_owned_endpoint()
        self.session=None;self.sequence=0
        self.rpc('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'emerald-native-cli','version':'1'}})
        self.rpc('notifications/initialized',notify=True)

    def verify_owned_endpoint(self):
        root=Path(__file__).resolve().parents[1]
        receipt=root/'out/native-editor/owned-process.json'
        if not receipt.exists():raise RuntimeError('No owned native-editor receipt; launch tools/native_editor.sh first')
        owner=json.loads(receipt.read_text());port=urlparse(self.url).port
        if owner['port']!=port or owner['project']!=str(root/'unreal/Emerald/Emerald.uproject'):
            raise RuntimeError('Endpoint does not match owned project receipt')
        result=subprocess.run(['lsof','-nP',f'-iTCP:{port}','-sTCP:LISTEN','-t'],capture_output=True,text=True)
        listeners={int(s) for s in result.stdout.split() if s.isdigit()}
        if listeners!={owner['pid']}:raise RuntimeError('Native port is not held by the task-owned engine PID')
        pid=str(owner['pid'])
        start=subprocess.check_output(['ps','-p',pid,'-o','lstart='],text=True).strip()
        command=subprocess.check_output(['ps','-p',pid,'-o','args='],text=True)
        executable=subprocess.check_output(['ps','-p',pid,'-o','comm='],text=True).strip()
        if start!=owner['start_identity'] or owner['project'] not in command or not executable.endswith('/UnrealEditor-Cmd'):
            raise RuntimeError('Owned engine identity changed; refusing native calls')

    def rpc(self,method,params=None,notify=False):
        self.verify_owned_endpoint()
        body={'jsonrpc':'2.0','method':method}
        if params is not None: body['params']=params
        if not notify:
            self.sequence+=1;body['id']=self.sequence
        headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
        if self.session: headers['Mcp-Session-Id']=self.session
        request=urllib.request.Request(self.url,json.dumps(body).encode(),headers)
        with urllib.request.urlopen(request,timeout=180) as response:
            self.session=response.headers.get('Mcp-Session-Id',self.session)
            text=response.read().decode()
        if not text.strip(): return None
        if text.lstrip().startswith('event:') or text.lstrip().startswith('data:'):
            text=next(line[5:].strip() for line in text.splitlines() if line.startswith('data:'))
        result=json.loads(text)
        if 'error' in result: raise RuntimeError(json.dumps(result['error']))
        return result.get('result')

    def tool(self,name,args):
        result=self.rpc('tools/call',{'name':name,'arguments':args})
        if result.get('isError'): raise RuntimeError(json.dumps(result))
        return result

if __name__=='__main__':
    client=NativeMCP();command=sys.argv[1] if len(sys.argv)>1 else 'list'
    if command=='list': result=client.tool('list_toolsets',{})
    elif command=='describe': result=client.tool('describe_toolset',{'toolset_name':sys.argv[2]})
    elif command=='call': result=client.tool('call_tool',{'toolset_name':sys.argv[2],'tool_name':sys.argv[3],'arguments':json.loads(sys.argv[4]) if len(sys.argv)>4 else {}})
    else: raise SystemExit('list | describe TOOLSET | call TOOLSET TOOL JSON')
    print(json.dumps(result,indent=2))
