#!/usr/bin/env python3
"""Check rendered-engine evidence for material fallbacks and runtime init errors."""
from pathlib import Path
import re
import sys

PATTERNS={
    'material_compile_failure':r'Failed to compile Material',
    'default_material_fallback':r'Default Material will be used',
    'python_initialization_error':r'LogPython: Error:',
    'engine_ensure':r'Ensure condition failed:',
    'fatal_error':r'Fatal error:'}

def verify(path):
    text=Path(path).read_text(errors='replace')
    findings={name:len(re.findall(pattern,text,re.I)) for name,pattern in PATTERNS.items()}
    if any(findings.values()):raise RuntimeError('Rendered engine log failed checks: '+str(findings))
    return findings

if __name__=='__main__':print('Verified rendered engine log:',verify(sys.argv[1]))
