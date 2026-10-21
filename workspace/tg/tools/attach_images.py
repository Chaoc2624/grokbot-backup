#!/usr/bin/env python3
"""Attach captured images to a digest JSON (hourly fragment, 6h block or daily.json). No AI, no text changes.
  tools/attach_images.py <digest.json> [--data-dir DIR] [--out PATH] [--max-extra N]
For each item, every '> 名：原话 {{time}}' speech line is matched to its source message(s): same group
(daily: the group given by the line's 【tag】, else any), sender name matches, time inside the {{t}} / {{t1~t2}}
token. Source messages that carry an 'image' (from tg_fetch) are added to item['images'] with "line" = the
exact speech line text (content is not modified). Up to --max-extra (default 8, 0 for daily) images of the
item's window that no line quotes are added with "line": null. Raw data is read from <data-dir>/<date>/hourly/*.json.
"""
import json, os, re, sys, glob
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'tools'))
from chatfmt import SPEECH
a = sys.argv[1:]; path = a[0]
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
data_dir = opt('--data-dir', os.path.join(BASE, 'data')); out = opt('--out', path)
doc = json.load(open(path)); date = doc['date']
daily = os.path.basename(path) == 'daily.json'
max_extra = int(opt('--max-extra', 0 if daily else 8))
if daily: hours = range(24)
else: h1, h2 = (int(x) for x in doc['window'].split('-')); hours = range(h1, h2)
groups = json.load(open(os.path.join(BASE, 'groups.json'))); tag2key = {g.get('tag'): g['key'] for g in groups}
n = lambda s: re.sub(r'\s+', '', s or '').lower()
msgs = {}
for h in hours:
    f = os.path.join(data_dir, date, 'hourly', f'{h:02d}.json')
    if not os.path.exists(f): continue
    for g in json.load(open(f))['groups']:
        for m in g['messages']: msgs.setdefault(g['key'], []).append(m)
TOK = re.compile(r'\{\{(\d{4}-\d\d-\d\d )?(\d\d:\d\d:\d\d)(?:~(\d\d:\d\d:\d\d))?\}\}\s*$')
TAGRX = re.compile(r'【([^】]{1,24})】')

def rec(g, m, line):
    i = m['image']
    return {'path': i['path'], 'thumb': i['thumb'], 'w': i.get('w'), 'h': i.get('h'), 'msg_id': m['id'], 'chat': g,
            'time': m['time'], 'sender': m.get('sender'), 'link': m.get('link'), 'line': line}

total = 0
for it in doc['items']:
    found, seen = [], set()
    for line in (it.get('content') or '').split('\n'):
        t = line.strip()
        sm = SPEECH.match(t) if t.startswith('>') else None
        tk = TOK.search(t)
        if not sm or not tk: continue
        t1 = date + ' ' + tk.group(2); t2 = date + ' ' + (tk.group(3) or tk.group(2))
        name = n(sm.group(1)); keys = [it['group']]
        if it['group'] not in msgs:
            tg = [tag2key[x] for x in TAGRX.findall(t) if x in tag2key]; keys = tg or list(msgs)
        for k in keys:
            for m in msgs.get(k, []):
                if 'image' not in m or not (t1 <= m['time'] <= t2): continue
                s = n(m.get('sender'))
                if not s or not (name in s or s in name): continue
                if (k, m['id']) in seen: continue
                seen.add((k, m['id'])); found.append(rec(k, m, t))
    if max_extra and it['group'] in msgs:
        for m in msgs[it['group']]:
            if len([x for x in found if x['line'] is None]) >= max_extra: break
            if 'image' in m and (it['group'], m['id']) not in seen:
                seen.add((it['group'], m['id'])); found.append(rec(it['group'], m, None))
    if found: it['images'] = found
    else: it.pop('images', None)
    total += len(found)
json.dump(doc, open(out, 'w'), ensure_ascii=False, indent=1)
print(out, total, 'image(s) attached,', sum(1 for it in doc['items'] for x in it.get('images', []) if x['line']), 'on speech lines')
