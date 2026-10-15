import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
def sub(a, b):
    global s
    assert s.count(a) == 1, (a[:60], s.count(a)); s = s.replace(a, b)

# 1. reord: hour sections newest first, topics newest first (零星消息 last), speech oldest first, 话题活跃成员 to section end
old_start = s.index('// reorder one content: speech rows newest-first')
old_end = s.index("const gtag=s=>")
s = s[:old_start] + r"""// reorder one content (2026-10-09 user rule): hour sections + topics NEWEST first (零星消息 last), speech rows
// inside a topic OLDEST first (by {{time}}; rows without a time keep their slot); '~ 话题活跃成员' to the end of its
// hour section; 网上核验 entries pulled out (shown in their own box). Daily '## 大类' sections keep their order.
function sortAsc(arr,key){const t=arr.filter(x=>key(x)).map((x,i)=>[x,i]);t.sort((a,b)=>key(a[0])<key(b[0])?-1:key(a[0])>key(b[0])?1:a[1]-b[1]);return t.map(x=>x[0])}
const isSp=l=>/^>\s*[^：:\n]{1,40}[：:]/.test(l.trim()),isDiv=t=>/^\*\*\d{1,2}:\d{2}\s*[–-]\s*\d{1,2}:\d{2}\*\*$/.test(t);
function ordTopics(ls){const pre=[],tps=[],act=[];
 for(const l of ls){const t=l.trim();if(!t)continue;if(/^~\s*话题活跃成员/.test(t)){act.push(l);continue}
  if(/^###\s/.test(t)){tps.push([l]);continue}(tps.length?tps[tps.length-1]:pre).push(l)}
 const done=tps.map((tp,k)=>{const b=tp.slice(1),idx=b.map((l,i)=>isSp(l)&&tkey(l)?i:-1).filter(i=>i>=0),sv=sortAsc(idx.map(i=>b[i]),tkey);idx.forEach((i,j)=>b[i]=sv[j]);
  const ch=b.findIndex(l=>/^~\s*涉及商家[：:]/.test(l.trim()));if(ch>0)b.unshift(b.splice(ch,1)[0]);
  const ks=b.map(tkey).filter(x=>x).sort();return {h:tp[0],b,k:ks.length?ks[ks.length-1]:'',i:k,z:/^###\s+零星消息/.test(tp[0].trim())}});
 const rest=done.filter(x=>!x.z),tm=rest.filter(x=>x.k).sort((a,b)=>a.k<b.k?1:a.k>b.k?-1:a.i-b.i);
 const out=[...pre];for(const x of tm.concat(rest.filter(x=>!x.k),done.filter(x=>x.z)))out.push(x.h,...x.b);return out.concat([...new Set(act)])}
function ordSection(ls){if(!ls.some(l=>/^#{1,2}\s/.test(l.trim())))return ordTopics(ls).join('\n');
 const parts=[[]];for(const l of ls){if(/^#{1,2}\s/.test(l.trim()))parts.push([l]);else parts[parts.length-1].push(l)}
 return parts.filter(p=>p.length).map(p=>{const h=/^#{1,2}\s/.test((p[0]||'').trim())?[p[0]]:[];return h.concat(ordTopics(p.slice(h.length))).join('\n')}).filter(x=>x.trim()).join('\n\n')}
function reord(c){const L=(c||'').split('\n'),body=[],ver=[];let inv=false;
 for(const l of L){const t=l.trim();
  if(isVH(t)){inv=true;continue}
  if(inv){if(isBound(t)){inv=false}else{if(/^[-*•]\s+/.test(t))ver.push(t);else if(t)ver.push('- '+t);continue}}
  body.push(l)}
 const secs=[{d:null,ls:[]}];for(const l of body){if(isDiv(l.trim()))secs.push({d:l.trim(),ls:[]});else secs[secs.length-1].ls.push(l)}
 const hk=d=>{const m=/(\d{1,2}):(\d{2})/.exec(d);return m?+m[1]*60+ +m[2]:0};
 const out=[];const h0=ordSection(secs[0].ls);if(h0.trim())out.push(h0);
 secs.slice(1).sort((a,b)=>hk(b.d)-hk(a.d)).forEach(x=>{const t=ordSection(x.ls);out.push(x.d+(t.trim()?'\n'+t:''))});
 return {body:out.join('\n\n').trim(),ver}}
""" + s[old_end:]

# 2. chips row for '~ 涉及商家：A · B'
sub("  else if(m=/^~\\s+(.*)/.exec(t)){close();out.push(`<div class=mt>${hli(m[1])}</div>`)}",
    "  else if(m=/^~\\s*涉及商家[：:]\\s*(.*)$/.exec(t)){close();const ms=m[1].split(/\\s+·\\s+/).map(x=>x.trim()).filter(x=>x);if(ms.length)out.push(`<div class=mc><span class=ml>涉及商家</span>${ms.map(x=>`<span class=mch>${x}</span>`).join('')}</div>`)}\n"
    "  else if(m=/^~\\s+(.*)/.exec(t)){close();out.push(`<div class=mt>${hli(m[1])}</div>`)}")
sub(".cv .mt{font-size:11.5px;color:#9aa1ab;margin:3px 0 2px 11px}",
    ".cv .mt{font-size:11.5px;color:#9aa1ab;margin:3px 0 2px 11px}\n"
    ".cv .mc{display:flex;flex-wrap:wrap;align-items:center;gap:4px 5px;margin:1px 0 5px 11px}"
    ".cv .mc .ml{font-size:11px;color:#9aa1ab;margin-right:2px}"
    ".cv .mc .mch{font-size:11.5px;line-height:19px;color:#374151;background:#f4f5f7;border:1px solid #e7e9ee;border-radius:10px;padding:0 8px;white-space:nowrap}"
    ".cv .mc .ml+.mch{color:#1a56c4;background:#eaf2ff;border-color:#d6e4fb}")

# 3. 6h blocks newest first inside a day; pull items (multi) newest first
sub(" for(const w of day.windows){const [a,b]=w.window.split('-');",
    " for(const w of [...day.windows].sort((x,y)=>y.window<x.window?-1:y.window>x.window?1:0)){const [a,b]=w.window.split('-');")
sub("  const multi=its.length>1,src=multi?its.map(it=>",
    "  const multi=its.length>1,src=multi?[...its].sort((x,y)=>(y.from||'')<(x.from||'')?-1:(y.from||'')>(x.from||'')?1:0).map(it=>")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
