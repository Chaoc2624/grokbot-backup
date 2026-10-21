#!/usr/bin/env python3
"""Append selected hourly-fragment topics into digests/<D>/daily.json (chat format, keeps {{}} tokens).
usage: daily_append.py <D> <plan.json> [--final] [--win-end 'YYYY-MM-DD HH:MM']
plan: [{"hour":"21","group":"waika","topic":"eSIM 推荐","section":"📱 SIM","max":7}, ...]
"""
import json, re, sys, os, glob
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D, plan = sys.argv[1], json.load(open(sys.argv[2]))
final = '--final' in sys.argv
we = sys.argv[sys.argv.index('--win-end') + 1] if '--win-end' in sys.argv else None
tags = {g['key']: g['tag'] for g in json.load(open(os.path.join(BASE, 'groups.json')))}
dpath = os.path.join(BASE, 'digests', D, 'daily.json')
daily = json.load(open(dpath)); item = daily['items'][0]; lines = item['content'].split('\n')

def topics(hh, grp):
    f = json.load(open(os.path.join(BASE, 'digests', D, 'hourly', f'{hh}.json')))
    for it in f['items']:
        if it['group'] != grp: continue
        cur = None; out = {}
        for l in (it.get('content') or '').split('\n'):
            if l.startswith('### '): cur = l[4:]; out[cur] = []
            elif l.startswith('~') or l.startswith('---'): cur = None if l.startswith('---') else cur
            elif cur and l.startswith('> '): out[cur].append(l)
        return out, it.get('verify') or ''
    return {}, ''

verifs = []
for p in plan:
    tp, ver = topics(p['hour'], p['group'])
    key = next((k for k in tp if k.startswith(p['topic'])), None)
    if not key: sys.exit(f"topic not found: {p}")
    m = re.match(r'^(.*?)\s*(\(\d+ 条 / \d+ 人\))?\s*$', key)
    title = f"### {m.group(1)}（{int(p['hour'])} 点） 【{tags[p['group']]}】" + (f" {m.group(2)}" if m.group(2) else '')
    if any(l.strip() == title for l in lines): continue
    body = tp[key][:p.get('max', 7)]
    sec = next((i for i, l in enumerate(lines) if l.startswith('## ') and p['section'] in l), None)
    if sec is None:   # create the section just before the 网上核验 heading
        names = {'今日要点': '## 🔥 今日要点', 'U 卡': '## 💳 U 卡 / 数字银行', '港卡': '## 🇭🇰 港卡 / 香港开户', '英区': '## 🇬🇧 英区 / 🇺🇸 美卡',
                 'SIM': '## 📱 SIM / eSIM / 漫游', '网络': '## 🖥 网络 / AI 订阅', '其他': '## 其他群友说法'}
        vi0 = next((i for i, l in enumerate(lines) if l.startswith('#### ') and '网上核验' in l), len(lines))
        lines[vi0:vi0] = [names.get(p['section'], '## ' + p['section']), '']; sec = vi0
    end = next((i for i in range(sec + 1, len(lines)) if lines[i].startswith('## ') or lines[i].startswith('#### ')), len(lines))
    while end > sec + 1 and not lines[end - 1].strip(): end -= 1
    lines[end:end] = [title] + body
    if ver:
        for v in ver.split('\n'):
            if v.strip().startswith('- ') and v not in verifs: verifs.append(v.strip())
vi = next(i for i, l in enumerate(lines) if l.startswith('#### ') and '网上核验' in l)
for v in verifs:
    if v not in lines: lines.append(v)
item['content'] = '\n'.join(lines)
if final: daily['partial'] = False
if we: daily['win_end'] = we
tot = 0
for f in glob.glob(os.path.join(BASE, 'data', D, 'hourly', '[0-9][0-9].json')):
    tot += sum(len(g['messages']) for g in json.load(open(f))['groups'])
item['msg_count'] = tot
json.dump(daily, open(dpath, 'w'), ensure_ascii=False, indent=1)
print(dpath, 'partial=', daily['partial'], 'win_end=', daily['win_end'], 'msgs=', tot, 'verify lines added=', len(verifs))
