#!/usr/bin/env python3
"""Fail closed on Unreal automation's report, even when engine exit code is zero."""
import argparse
import json
from pathlib import Path


def verify(path: Path, expected: str):
    data=json.loads(path.read_text(encoding='utf-8-sig'))
    tests=[t for t in data.get('tests',[]) if t.get('fullTestPath','').startswith(expected)]
    if not tests:
        raise RuntimeError('No matching Unreal tests actually ran')
    for test in tests:
        if test.get('state') != 'Success':
            raise RuntimeError(test.get('fullTestPath','unknown')+' state='+str(test.get('state')))
        for entry in test.get('entries',[]):
            if entry.get('event',{}).get('type')=='Error':
                raise RuntimeError('Error event in '+test['fullTestPath'])
    if data.get('failed',0) or data.get('notRun',0) or data.get('inProcess',0):
        raise RuntimeError('Failed, incomplete or unrun tests remain')
    return len(tests)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('report',type=Path)
    p.add_argument('--prefix',default='Emerald.Data')
    a=p.parse_args()
    print('Verified Unreal automation:',verify(a.report,a.prefix),'passed tests')
