#!/usr/bin/env python3
"""Write a digest fragment from a spec on stdin.

  tools/mkfrag.py 2026-10-08 18      < spec   -> digests/2026-10-08/hourly/18.json  (window 18-19)
  tools/mkfrag.py 2026-10-08 15-18   < spec   -> digests/2026-10-08/3h/15-18.json   (window 15-18)

spec: blocks starting with a line '=== <group key>' followed by chat-format lines (see tools/chatfmt.py):
'### 话题 (N 条 / M 人)', '> 发言人：原话' (verbatim; ==关键词== optional, auto-added when a line has none),
'~ 话题活跃成员（近 7 天话题消息）：…', '### 零星消息'. Members' words only.
Inside a block, a line '--- 核验' starts that group's web-verification bullets (external sources only,
e.g. '- 万里汇英区 £50｜WorldFirst 官网（2026-10-08 查阅）：页面写明 … https://…'); they are stored as item['verify'] and
tg_merge6h.py renders them in a separate 「🔎 网上核验」 section.
Title and msg_count are filled in automatically from groups.json and the fetched data file
(data/<date>/hourly/<HH>.json or data/<date>/<HH-HH>.json). Groups missing from the spec, or with an
empty block, get '无重要内容'. Optional '=== key|title|count' (mk.py style) is accepted; count overrides.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chatfmt import canon, lint
from order import order_content   # newest-first topics / oldest-first lines / 涉及商家
from datetime import datetime, timedelta
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
date, win = sys.argv[1], sys.argv[2]
if '-' in win:
    h1, h2 = (int(x) for x in win.split('-')); out = os.path.join(BASE, 'digests', date, '3h', f'{h1:02d}-{h2:02d}.json')
    src = os.path.join(BASE, 'data', date, f'{h1:02d}-{h2:02d}.json')
else:
    h1 = int(win); h2 = h1 + 1; out = os.path.join(BASE, 'digests', date, 'hourly', f'{h1:02d}.json')
    src = os.path.join(BASE, 'data', date, 'hourly', f'{h1:02d}.json')
groups = json.load(open(os.path.join(BASE, 'groups.json')))
counts = {}
if os.path.exists(src):
    for g in json.load(open(src))['groups']: counts[g['key']] = g['count']
else:
    print(f'warning: {src} missing, msg_count=0', file=sys.stderr)
spec, cur = {}, None
for line in sys.stdin.read().split('\n'):
    if line.startswith('=== '):
        parts = line[4:].strip().split('|'); cur = parts[0].strip()
        spec[cur] = {'lines': [], 'verify': [], 'in_v': False, 'count': int(parts[2]) if len(parts) > 2 and parts[2].strip() else None}
    elif cur is not None and line.strip() in ('--- 核验', '---核验', '--- verify'): spec[cur]['in_v'] = True
    elif cur is not None:
        if spec[cur]['in_v']: spec[cur]['verify'].append(line)
        else:
            w = lint(line)
            if w: print(f'warning [{cur}] {w}: {line.strip()[:80]}', file=sys.stderr)
            spec[cur]['lines'].append(canon(line))
unknown = set(spec) - {g['key'] for g in groups}
if unknown: sys.exit(f'unknown group keys: {unknown}')
items = []
for g in sorted(groups, key=lambda g: g.get('order') or 999):
    s = spec.get(g['key'], {'lines': [], 'verify': [], 'count': None})
    it = {'group': g['key'], 'title': g['title'], 'msg_count': s['count'] if s['count'] is not None else counts.get(g['key'], 0),
          'content': order_content('\n'.join(s['lines']).strip()) or '无重要内容'}
    v = '\n'.join(s['verify']).strip()
    if v: it['verify'] = v
    items.append(it)
d = {'date': date, 'window': f'{h1:02d}-{h2:02d}', 'partial': False,
     'win_start': f'{date} {h1:02d}:00',
     'win_end': (datetime.strptime(date, '%Y-%m-%d') + timedelta(hours=h2)).strftime('%Y-%m-%d %H:%M'), 'items': items}
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump(d, open(out, 'w'), ensure_ascii=False, indent=1)
print(out, ' '.join(f"{i['group']}={i['msg_count']}{'(无)' if i['content'] == '无重要内容' else ''}{'+核验' if i.get('verify') else ''}" for i in items))
