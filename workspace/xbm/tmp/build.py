import json,datetime,sys
run_at=sys.argv[1]
exec(open('tmp/items-20261015-am.py').read()); exec(open('tmp/radar-items.py').read())
raw=json.load(open('raw-20261015-am.json'))
seen=set(l.strip() for l in open('seen.txt') if l.strip())
users={u['id']:u['username'] for u in raw['includes'].get('users',[])}
new=[p for p in raw['data'] if p['id'] not in seen]
order={'urgent':0,'related':1,'needs':2,'ads':3}
items=[]
for p in new:
    tag,title,need,action,dl,due,cat,prio=I[p['id']]
    ct=datetime.datetime.fromisoformat(p['created_at'].replace('Z','+00:00'))+datetime.timedelta(hours=8)
    it={"id":p['id'],"url":f"https://x.com/i/status/{p['id']}","title":title,"tag":tag,"need":need,"action":action,
        "deadline":dl,"due_date":due or None,"category":cat,"posted_at":f"{ct:%m-%d %H:%M}"}
    if prio: it["priority"]=prio
    items.append(it)
items.sort(key=lambda x:(order[x['category']], 1 if x.get('priority')=='low' else 0))
carry=json.load(open('carryover-20261015-am.json'))
carried=[c['id'] for c in carry if c['id'] not in {i['id'] for i in items}]
label="2026-10-15 上午"
json.dump({"label":label,"items":items,"carried_ids":carried},open('ingest-20261015-am.json','w'),ensure_ascii=False,indent=1)
summary=("补跑 10-09 晚上之后漏掉的几次（10-14 晚上那次失败了），新增 66 条书签。最急的两条：MLH 黑客周免费 Cursor Pro 今天截止，IBKR 不交地址证明就能开户的放水窗口。"
 "其余集中在美卡起步（Discover/C1/Citi/汇丰/Kikoff）、ITIN 注册 IRS 账户、中银香港开户顺序、翻墙泄漏和家宽、建站词与 GEO（新词雷达开源、出单复盘），以及 Agent 工具。"
 f"另有 {len(carried)} 条之前推过、还没处理。AI 侧：Gemini 4 Argon 全球上线、Meta Muse Wonder、Grok+Cursor 合并成 The X Subscription。")
json.dump({"label":label,"run_at":run_at,"summary":summary,"new_ids":[i['id'] for i in items],"carried_ids":carried},open('briefsync-20261015-am.json','w'),ensure_ascii=False,indent=1)
kws=[{"keyword":r["keyword"],"reason":r["reason"]} for r in sorted([r for r in R if r.get("keyword_rank")],key=lambda r:r["keyword_rank"])]
json.dump({"label":label,"run_at":run_at,"window_start":"2026-10-09 22:39","window_end":run_at,"empty":len(R)==0,"items":R,"keywords":kws},open('radar-2026-10-15-am.json','w'),ensure_ascii=False,indent=1)
from collections import Counter
print(len(items),len(carried),len(R),Counter(i['category']+'/'+i.get('priority','') for i in items))
