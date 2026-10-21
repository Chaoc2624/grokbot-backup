import json,sys
# usage: python mk.py out.json date window partial win_start win_end  < spec (blocks separated by lines '=== key|title|count')
out,date,win,partial,ws,we=sys.argv[1:7]
items=[];cur=None
for line in sys.stdin.read().split('\n'):
    if line.startswith('=== '):
        k,t,c=line[4:].split('|'); cur={'group':k,'title':t,'msg_count':int(c),'content':''}; items.append(cur)
    elif cur is not None: cur['content']+=line+'\n'
for it in items: it['content']=it['content'].strip() or '无重要内容'
json.dump({'date':date,'window':win,'partial':partial=='1','win_start':ws,'win_end':we,'items':items},open(out,'w'),ensure_ascii=False,indent=1)
print(out,len(items))
