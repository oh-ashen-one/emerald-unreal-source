#!/usr/bin/env python3
"""Compile pret source labels to lossless runtime IR; no ROM/bytecode required."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
try:
    from .import_littleroot import Importer,ROOT
except ImportError:
    from import_littleroot import Importer,ROOT


def split_args(text):
    result=[];start=0;depth=0;quote=False;escape=False
    for i,c in enumerate(text):
        if escape:escape=False;continue
        if c=='\\':escape=True;continue
        if c=='"':quote=not quote
        if not quote:
            if c=='(':depth+=1
            elif c==')':depth-=1
            elif c==',' and depth==0:result.append(text[start:i].strip());start=i+1
    if text[start:].strip():result.append(text[start:].strip())
    return result


def strip_comment(line):
    quote=False;escape=False
    for i,c in enumerate(line):
        if escape:escape=False;continue
        if c=='\\':escape=True;continue
        if c=='"':quote=not quote
        elif c=='@' and not quote:return line[:i]
    return line


def text_value(body):
    values=re.findall(r'\.string\s+"((?:\\.|[^"\\])*)"',body)
    return ''.join(values).replace('\\n','\n').replace('\\l','\n').replace('\\p','\f').replace('\\"','"').replace("\\'","'").removesuffix('$')


def const_eval(expression,known):
    expression=re.sub(r'\b(0x[0-9A-Fa-f]+|[0-9]+)[uUlL]+\b',r'\1',expression.strip())
    expression=re.sub(r'\bTRUE\b','1',expression)
    expression=re.sub(r'\bFALSE\b','0',expression)
    node=ast.parse(expression,mode='eval').body
    def visit(n):
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,bool)):return int(n.value)
        if isinstance(n,ast.Name):return known[n.id]
        if isinstance(n,ast.UnaryOp):
            x=visit(n.operand)
            if isinstance(n.op,ast.USub):return -x
            if isinstance(n.op,ast.UAdd):return x
            if isinstance(n.op,ast.Invert):return ~x
        if isinstance(n,ast.BinOp):
            a,b=visit(n.left),visit(n.right)
            for cls,fn in [(ast.Add,lambda:a+b),(ast.Sub,lambda:a-b),(ast.Mult,lambda:a*b),(ast.Div,lambda:a//b),(ast.FloorDiv,lambda:a//b),(ast.Mod,lambda:a%b),(ast.LShift,lambda:a<<b),(ast.RShift,lambda:a>>b),(ast.BitOr,lambda:a|b),(ast.BitAnd,lambda:a&b),(ast.BitXor,lambda:a^b)]:
                if isinstance(n.op,cls):return fn()
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='BIT' and len(n.args)==1:return 1<<visit(n.args[0])
        raise ValueError('Unsupported C constant expression')
    return visit(node)


def constants(source,hashes):
    definitions={};known={}
    for path in sorted((source/'include/constants').glob('*.h')):
        raw=path.read_bytes();hashes[str(path.relative_to(source))]=hashlib.sha256(raw).hexdigest()
        text=re.sub(r'/\*.*?\*/|//[^\n]*','',raw.decode(),flags=re.S).replace('\\\n',' ')
        for name,expr in re.findall(r'^\s*#define\s+(\w+)[ \t]+([^\n]+)',text,re.M):definitions[name]=expr.strip()
        for enum in re.findall(r'enum(?:\s+\w+)?\s*\{([^}]+)\}',text,re.S):
            previous=None
            for entry in enum.split(','):
                entry=entry.strip()
                if not entry:continue
                if '=' in entry:name,expr=entry.split('=',1)
                else:name,expr=entry,('0' if previous is None else previous+' + 1')
                name=name.strip()
                if re.fullmatch(r'\w+',name):definitions[name]=expr.strip();previous=name
    for _ in range(40):
        before=len(known)
        for name,expr in definitions.items():
            if name in known:continue
            try:known[name]=const_eval(expr,known)
            except (ValueError,KeyError,SyntaxError,TypeError,ZeroDivisionError):pass
        if len(known)==before:break
    return known


def movement_contract(source,hashes,const):
    paths=['src/event_object_movement.c','src/data/object_events/movement_type_func_tables.h','src/metatile_behavior.c','include/random.h']
    raw={name:(source/name).read_text() for name in paths}
    for name in paths:hashes[name]=hashlib.sha256((source/name).read_bytes()).hexdigest()
    movement=raw[paths[0]];tables=raw[paths[1]]
    def array(text,name):
        body=re.search(r'\b'+name+r'\[[^]]*\]\s*=\s*\{(.*?)\};',text,re.S)[1]
        return [const_eval(x.strip(),const) for x in body.split(',') if x.strip()]
    def mapping(name):
        body=re.search(r'\b'+name+r'\[[^]]*\]\s*=\s*\{(.*?)\};',movement,re.S)[1]
        return {k:const_eval(v.strip(),const) for k,v in re.findall(r'\[(\w+)\]\s*=\s*([^,]+)',body)}
    blocked={}
    for name in ('North','South','East','West'):
        body=re.search(r'bool8 MetatileBehavior_Is'+name+r'Blocked\(.*?\)\s*\{(.*?)\n\}',raw[paths[2]],re.S)[1]
        blocked[name.lower()]=[const[x] for x in re.findall(r'metatileBehavior == (\w+)',body)]
    rng=re.search(r'#define ISO_RANDOMIZE1\(val\) \((\d+) \* \(val\) \+ (\d+)\)',raw[paths[3]])
    steps=re.search(r'sStep1Funcs\[\]\s*=\s*\{(.*?)\};',movement,re.S)[1]
    return {'delay_frames':array(movement,'sMovementDelaysMedium'),'directions':array(tables,'gStandardDirections'),
            'horizontal_directions':array(tables,'gLeftAndRightDirections'),'vertical_directions':array(tables,'gUpAndDownDirections'),
            'initial_facing':mapping('gInitialMovementTypeFacingDirections'),'has_range':mapping('sMovementTypeHasRange'),
            'blocked_behaviors':blocked,'walk_frames':len(re.findall(r'\bStep1\b',steps)),
            'rng_multiplier':int(rng[1]),'rng_increment':int(rng[2]),'rng_seed':0,'frames_per_second':60}


def compile_program(source=ROOT/'pokeemerald'):
    importer=Importer(source);data=importer.run()
    roots=[m['name']+'_MapScripts' for m in data['maps']]
    for m in data['maps']:
        for key in ('object_events','coord_events','bg_events'):
            roots.extend(e['script'] for e in m[key] if e.get('script') not in (None,'0x0','0'))
    roots+=['EventScript_ResetAllMapFlags','InsideOfTruck_EventScript_SetIntroFlagsMale','InsideOfTruck_EventScript_SetIntroFlagsFemale']
    scripts,missing=importer.scripts(roots)
    hashes=dict(importer.inputs);const=constants(source,hashes);labels={};texts={};ops=Counter();callbacks={}
    for name,item in scripts.items():
        body=item['body'];commands=[]
        if re.search(r'^\s*\.string\b',body,re.M):
            texts[name]=text_value(body)
            continue
        for offset,line in enumerate(body.splitlines()):
            line=strip_comment(line).strip()
            if not line:continue
            op,*tail=line.split(None,1)
            args=split_args(tail[0]) if tail else []
            commands.append({'op':op,'args':args,'line':item['line']+1+offset});ops[op]+=1
        labels[name]={'source':item['source'],'line':item['line'],'next':item['next_label'],'commands':commands}
    central=source/'data/event_scripts.s'
    raw=central.read_bytes();hashes['data/event_scripts.s']=hashlib.sha256(raw).hexdigest()
    matches=list(re.finditer(r'^(\w+)::?[^\n]*\n',raw.decode(),re.M))
    central_text=raw.decode()
    for i,match in enumerate(matches):
        end=matches[i+1].start() if i+1<len(matches) else len(central_text)
        body=central_text[match.end():end]
        if re.search(r'^\s*\.string\b',body,re.M):texts[match[1]]=text_value(body)
    # Some event messages are C string constants rather than script .string data.
    for path in [source/'src/strings.c',*sorted((source/'src/data').rglob('*pokedex*.h'))]:
        if not path.exists():continue
        raw=path.read_bytes();hashes[str(path.relative_to(source))]=hashlib.sha256(raw).hexdigest()
        for name,body in re.findall(r'const\s+u8\s+(\w+)\[\]\s*=\s*_\((.*?)\);',raw.decode(),re.S):
            quotes=re.findall(r'"((?:\\.|[^"\\])*)"',body)
            texts[name]=text_value('\n'.join('.string "'+q+'"' for q in quotes))
    for m in data['maps']:
        callbacks[m['id']]={}
        for cmd in labels[m['name']+'_MapScripts']['commands']:
            if cmd['op']=='map_script':callbacks[m['id']][cmd['args'][0]]=cmd['args'][1]
    initial=[c['args'][0] for c in labels['EventScript_ResetAllMapFlags']['commands'] if c['op']=='setflag']
    local_ids={m['id']:{e['local_id']:i+1 for i,e in enumerate(m['object_events']) if 'local_id' in e} for m in data['maps']}
    unresolved_texts=sorted({c['args'][0] for l in labels.values() for c in l['commands'] if c['op'] in ('msgbox','message') and c['args'] and c['args'][0] not in texts})
    unresolved_branches=set()
    for label in labels.values():
        for cmd in label['commands']:
            op=cmd['op'];args=cmd['args']
            if not args:continue
            target=(args[0] if op in ('goto','call') else args[-1] if op.startswith(('goto_if_','call_if_')) or op in ('map_script','map_script_2') else args[1] if op in ('applymovement','applywaitmovement') and len(args)>1 else None)
            if target and target not in labels:unresolved_branches.add(target)
    return {'schema':'emerald.source-events/1','source_revision':data['source_revision'],'constants':const,'labels':labels,'texts':texts,
            'movement_contract':movement_contract(source,hashes,const),'callbacks':callbacks,'local_ids':local_ids,'initial_flags':initial,'source_hashes':hashes,
            'missing_roots':missing,'unresolved_branch_labels':sorted(unresolved_branches),'unresolved_message_labels':unresolved_texts,'opcode_counts':dict(ops)}

if __name__=='__main__':
    program=compile_program();output=ROOT/'unreal/Emerald/Content/Imported/Data/source-events.json'
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(program,indent=2)+'\n')
    (ROOT/'data/event-source-lock.json').write_text(json.dumps({'source_revision':program['source_revision'],'hashes':program['source_hashes']},indent=2)+'\n')
    summary={k:program[k] for k in ['source_revision','missing_roots','unresolved_branch_labels','unresolved_message_labels','opcode_counts']}
    summary['movement_contract']=program['movement_contract']
    summary.update(labels=len(program['labels']),texts=len(program['texts']),constants=len(program['constants']),initial_flags=len(program['initial_flags']),runtime_parity_verified=False)
    (ROOT/'data/event-import-report.json').write_text(json.dumps(summary,indent=2)+'\n')
    print({k:v for k,v in summary.items() if k not in ('opcode_counts','movement_contract')})
