import json,datetime,sys
run_at=sys.argv[1]
exec(open('tmp/items-20261015-pm.py').read()); exec(open('tmp/radar-items-pm.py').read())
d=json.load(open('new-20261015-pm.json'))
order={'urgent':0,'related':1,'needs':2,'ads':3}
items=[]
for p in d['data']:
    tag,title,need,action,dl,due,cat,prio=I[p['id']]
    ct=datetime.datetime.fromisoformat(p['created_at'].replace('Z','+00:00'))+datetime.timedelta(hours=8)
    it={"id":p['id'],"url":f"https://x.com/i/status/{p['id']}","title":title,"tag":tag,"need":need,"action":action,
        "deadline":dl,"due_date":due,"category":cat,"posted_at":f"{ct:%m-%d %H:%M}"}
    if prio: it["priority"]=prio
    items.append(it)
items.sort(key=lambda x:(order[x['category']], 1 if x.get('priority')=='low' else 0))
carry=json.load(open('carryover-20261015-pm.json'))
carried=[c['id'] for c in carry if c['id'] not in {i['id'] for i in items}]
label="2026-10-15 晚上"
json.dump({"label":label,"items":items,"carried_ids":carried},open('ingest-20261015-pm.json','w'),ensure_ascii=False,indent=1)
summary=("新增 9 条书签，没有今天必须处理的新事。主要是美卡（C1 激活后 7 项设置、C1 批卡时间线、ATMB 地址要查房号）、港币回内地两条路子、Lebara/DITO 连过内地基站就拉不起 WiFi Calling、Stripe Radar 防欺诈规则。"
 f"MLH 黑客周领 Cursor Pro 今晚截止，还没领的话抓紧。另有 {len(carried)} 条之前推过、还没处理。AI 侧：OpenCode 免费开放 DeepSeek V4.1 Flash、阶跃 Step 5 Preview 开源、Ultramarine 1 Flash。")
json.dump({"label":label,"run_at":run_at,"summary":summary,"new_ids":[i['id'] for i in items],"carried_ids":carried},open('briefsync-20261015-pm.json','w'),ensure_ascii=False,indent=1)
kws=[{"keyword":r["keyword"],"reason":r["reason"]} for r in sorted([r for r in R if r.get("keyword_rank")],key=lambda r:r["keyword_rank"])]
json.dump({"label":label,"run_at":run_at,"window_start":"2026-10-15 10:11","window_end":run_at,"empty":len(R)==0,"items":R,"keywords":kws},open('radar-2026-10-15-pm.json','w'),ensure_ascii=False,indent=1)
print(len(items),len(carried),len(R),len(kws))
