import json,sys,re
for f,kw in [(a.split('=')[0],a.split('=')[1] if '=' in a else '') for a in sys.argv[1:]]:
    raw=open(f).read()
    try: d=json.loads(raw.split('\nX reads')[0])
    except Exception:
        m=raw.find('{'); d=json.JSONDecoder().raw_decode(raw[m:])[0]
    print('=====',f, 'n=',len(d.get('data',[])))
    for p in d.get('data',[]):
        t=(p.get('note_tweet',{}) or {}).get('text') or p.get('text','')
        if kw and not re.search(kw,t,re.I): continue
        urls=[u.get('expanded_url') for u in ((p.get('note_tweet') or {}).get('entities') or p.get('entities') or {}).get('urls',[])]
        print('-',p['id'],p.get('created_at'),'conv',p.get('conversation_id'),'|',t[:500].replace('\n',' '),'| URLS',' '.join(x for x in urls if x and '/photo/' not in x and '/video/' not in x))
