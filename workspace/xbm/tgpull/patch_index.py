import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:80], s.count(a)); s = s.replace(a, b)
js = open('/tmp/pull.js').read().replace("if(TGS.job&&TGS.job.status=='running'&&!PJT)pjPoll(TGS.job.id)", "if(TGS.job&&!PJ)PJ=TGS.job;if(TGS.job&&TGS.job.status=='running'&&!PJT)pjPoll(TGS.job.id)").replace("if(k=='q'&&!v&&PM.v==null)PM.v='h6';\n", "")
js = js.replace("const long=(m.text||'').length>360||(m.text||'').split('\\n').length>8;", "const long=(m.text||'').length>240||(m.text||'').split('\\n').length>6;")
css = open('/tmp/pull.css').read().replace(".br.tgr{padding:10px 14px}", ".br.tgr{padding:10px 14px}\n.tgr .bh{padding-right:96px;min-height:22px}").replace("-webkit-line-clamp:8;", "-webkit-line-clamp:6;").replace(" .pgi .m{display:none}", " .pgi .m{display:none}.ppf .pgr{display:none}")
rep("</style></head><body>", css + "</style></head><body>")
rep("<script>\nconst V=[", "<script>\nif(location.hash=='#tg-login')location.replace('tg-login');\nconst V=[")
rep("window.onhashchange=()=>{view=HV(location.hash.slice(1));load()};load();",
    "window.onhashchange=()=>{if(location.hash=='#tg-login')return location.replace('tg-login');view=HV(location.hash.slice(1));load()};load();")
rep("async function u(id,b,quiet){", js + "async function u(id,b,quiet){")
rep("const r=await fetch('api/tg'+qs);if(r.status==401)return location.reload();const d=await r.json();GX={};let gid=0;",
    "const sp0=tgStat();const r=await fetch('api/tg'+qs);if(r.status==401)return location.reload();const d=await r.json();GX={};let gid=0;const RW=await rawFetch(d);await sp0;")
rep("""${[['1','今天'],['3','3天'],['7','7天'],['all','全部']].map(([k,l])=>`<button class="${GR==k?'on':''}" onclick="gset('gr','${k}')">${k=='1'&&GD!=d.today?'当天':l}</button>`).join('')}</div>`;""",
    """${[['1','今天'],['3','3天'],['7','7天'],['all','全部']].map(([k,l])=>`<button class="${GR==k?'on':''}" onclick="gset('gr','${k}')">${k=='1'&&GD!=d.today?'当天':l}</button>`).join('')}${pullBtn()}</div><div id=pullbar>${pullBar()}</div>`;""")
rep("""${nw} 个时段 · ${nm} 条消息</span></div>`;""", """${nw} 个时段 · ${nm} 条消息${RW.total?` · 实时拉取 ${nf(RW.total)} 条`:''}</span></div>`;""")
rep("""if(!d.days.length){document.getElementById('list').innerHTML=h+'<div class=rbox><div class=emp>这段时间还没有群总结。</div></div>';return}""",
    """if(!d.days.length&&!RW.days.length){document.getElementById('list').innerHTML=h+'<div class=rbox><div class=emp>这段时间还没有群总结。</div></div>';return}""")
rep("""for(const day of d.days){CHD=day.date;h+=`<div class=day>${day.date}</div>`;""",
    """const RM={},DM={};RW.days.forEach(x=>RM[x.date]=x);d.days.forEach(x=>DM[x.date]=x);
for(const dd of [...new Set([...d.days.map(x=>x.date),...RW.days.map(x=>x.date)])].sort().reverse()){const day=DM[dd]||{date:dd,daily:null,windows:[]};CHD=day.date;h+=`<div class=day>${day.date}</div>`;if(RM[dd])h+=rawCard(RM[dd]);""")
i = s.index('async function tg(){'); e = "document.getElementById('list').innerHTML=h}"; j = s.index(e, i)
s = s[:j] + "document.getElementById('list').innerHTML=h;rawRestore()}" + s[j + len(e):]
open(dst, 'w').write(s)
print('patched', dst)
