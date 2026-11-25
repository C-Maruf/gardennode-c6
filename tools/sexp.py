import re
_tok = re.compile(r'\s*(\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+)')
class Sym(str): pass
def parse(s):
    pos=0; stack=[[]]
    for m in _tok.finditer(s):
        t=m.group(1)
        if t=='(':
            stack.append([])
        elif t==')':
            x=stack.pop(); stack[-1].append(x)
        elif t.startswith('"'):
            stack[-1].append(t[1:-1].replace('\\"','"').replace('\\\\','\\'))
        else:
            stack[-1].append(Sym(t))
    return stack[0]
def dump(x, ind=0):
    if isinstance(x,list):
        if all(not isinstance(i,list) for i in x):
            return '('+' '.join(dump(i) for i in x)+')'
        out='('+dump(x[0]) if x else '('
        for i in x[1:]:
            if isinstance(i,list): out+='\n'+'  '*(ind+1)+dump(i,ind+1)
            else: out+=' '+dump(i)
        return out+')'
    if isinstance(x,Sym): return str(x)
    if isinstance(x,(int,float)): 
        return ('%.4f'%x).rstrip('0').rstrip('.') if isinstance(x,float) else str(x)
    return '"'+str(x).replace('\\','\\\\').replace('"','\\"')+'"'
def find(x, key):
    return [i for i in x if isinstance(i,list) and i and i[0]==key]
def find1(x,key):
    r=find(x,key); return r[0] if r else None
_libcache={}
def load_lib(path):
    if path not in _libcache:
        tree=downgrade(parse(open(path).read())[0])
        _libcache[path]={s[1]:s for s in find(tree,'symbol')}
    return _libcache[path]
def get_symbol(path, name):
    """returns flattened symbol s-expr (deep copy) with name"""
    import copy
    lib=load_lib(path); s=copy.deepcopy(lib[name])
    ext=find1(s,'extends')
    if ext:
        parent=get_symbol(path, ext[1])
        # rename parent's unit subsymbols
        newp=[Sym('symbol'), name]
        props={p[1]:p for p in find(s,'property')}
        for item in parent[2:]:
            if isinstance(item,list) and item[0]=='property' and item[1] in props:
                newp.append(props.pop(item[1]))
            elif isinstance(item,list) and item[0]=='symbol':
                item=copy.deepcopy(item); item[1]=item[1].replace(ext[1],name,1); newp.append(item)
            else: newp.append(item)
        for p in props.values(): newp.insert(-1,p)
        s=newp
    return s
def pins(sym):
    out=[]
    def walk(x):
        for i in x:
            if isinstance(i,list):
                if i and i[0]=='pin':
                    at=find1(i,'at'); nm=find1(i,'name'); nu=find1(i,'number')
                    hidden = any(isinstance(k,Sym) and k=='hide' for k in i)
                    out.append(dict(type=str(i[1]),x=float(at[1]),y=float(at[2]),rot=float(at[3]) if len(at)>3 else 0,name=nm[1],num=nu[1],hidden=hidden))
                else: walk(i)
    walk(sym); return out

DROP = {'exclude_from_sim','embedded_fonts','generator_version','duplicate_pin_numbers_are_jumpers','jumper_pin_groups',
        'in_pos_files','show_name','do_not_autoplace','body_styles'}
def downgrade(x):
    """convert KiCad 8/9 symbol s-expr to KiCad 7 syntax"""
    if not isinstance(x, list): return x
    out=[]; hide=False
    for i in x:
        if isinstance(i,list) and i and i[0] in DROP: continue
        if isinstance(i,list) and i and i[0]=='hide' and len(i)==2:
            hide = (i[1]=='yes'); continue
        out.append(downgrade(i))
    if hide:
        if out and out[0]=='property':
            for e in out:
                if isinstance(e,list) and e and e[0]=='effects': e.append(Sym('hide')); break
        else:
            out.append(Sym('hide'))
    if out and out[0] in ('stroke',) :
        pass
    return out
