import re,ipaddress,sys,collections
L=open(sys.argv[1],encoding='utf-8').read().split('\n')
sec=None; secs=collections.Counter(); S=collections.defaultdict(list)
for i,l in enumerate(L,1):
    s=l.strip()
    m=re.match(r'^\[(.+)\]$',s)
    if m: sec=m.group(1); secs[sec]+=1; continue
    if not s or s.startswith('#') or s.startswith('//'): continue
    S[sec].append((i,s))
print("dup sections:",[k for k,v in secs.items() if v>1])
# dup keys in General/Mitm
for sname in ['General','Mitm']:
    c=collections.defaultdict(list)
    for i,s in S[sname]: c[s.split('=')[0].strip()].append(i)
    print(sname,"dup keys:",{k:v for k,v in c.items() if len(v)>1})
groups={s.split('=')[0].strip() for i,s in S['Proxy Group']}
filters={s.split('=')[0].strip() for i,s in S['Remote Filter']}
builtin={'DIRECT','REJECT','REJECT-DROP','REJECT-TINYGIF','REJECT-IMG','REJECT-DICT','REJECT-ARRAY','REJECT-200','PROXY','REJECT-NO-DROP'}
known=groups|filters|builtin
for i,s in S['Proxy Group']:
    name,rest=s.split('=',1); parts=[p.strip() for p in rest.split(',')]
    for p in parts[1:]:
        if '=' in p: continue
        if p not in known: print("GROUP undefined member",i,name.strip(),p)
types=collections.Counter(); bad=[]
nodes_dom=['tube-cat.com','catcat321.com','omnitools.cc','bilibili.com','microsoft.com','cloudflare.com','gstatic.com','hicloud.com','raw.githubusercontent.com','githubusercontent.com','github.com','kelee.one','0b96e976-9ec3-44c0-aa2b-30bf8b0792ea.com']
ips=[ipaddress.ip_address(x) for x in '218.33.111.30 218.33.111.31 157.254.38.210 104.21.72.195 172.67.154.141 13.215.219.205 107.149.159.229 1.1.1.1 1.0.0.1 119.29.29.29'.split()]
pol=collections.Counter()
for i,s in S['Rule']:
    parts=[p.strip() for p in s.split(',')]
    t=parts[0].upper(); types[t]+=1
    if t=='FINAL': p=parts[1]
    elif t in('AND','OR','NOT'):
        p=re.split(r'\)\s*,',s)[-1].split(',')[0].strip()
    else:
        if len(parts)<3: bad.append((i,s)); continue
        p=parts[2]
    pol[p]+=1
    if p not in known: print("RULE undefined policy",i,s[:120])
    if t in('DOMAIN','DOMAIN-SUFFIX'):
        v=parts[1].lower()
        for d in nodes_dom:
            if d==v or d.endswith('.'+v) or v.endswith('.'+d) : print("RULE hits node/infra domain",i,s)
    if t=='DOMAIN-KEYWORD':
        for d in nodes_dom:
            if parts[1].lower() in d: print("RULE keyword hits",i,s)
    if t in('IP-CIDR','IP-CIDR6'):
        try:
            n=ipaddress.ip_network(parts[1],strict=False)
            for a in ips:
                if a.version==n.version and a in n: print("RULE IP hit",i,s,a)
        except Exception as e: bad.append((i,s))
print("rule types",dict(types)); print("policies",dict(pol)); print("malformed",bad[:20],len(bad))
# Host
for i,s in S['Host']:
    print("HOST",i,s) if any(d in s for d in nodes_dom) else None
