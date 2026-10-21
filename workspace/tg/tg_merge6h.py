#!/usr/bin/env python3
"""Build a fixed 6-hour board block (00-06 / 06-12 / 12-18 / 18-24, Asia/Shanghai) from digest fragments.

  tg_merge6h.py --date 2026-10-08 --block 18-24 [--push]
  tg_merge6h.py --block lasthour --push     # the block that contains the last completed hour
                                            #   (at 00:xx -> previous day's 18-24)
  tg_merge6h.py --date 2026-10-08 --all [--push]   # every block of that day that has fragments
  add --dry-run to print the merged block instead of writing it.

Fragments (one item per group, same format as board digests):
  digests/<date>/hourly/<HH>.json   window HH-(HH+1)   (written by tools/mkfrag.py <date> <HH>)
  digests/<date>/3h/<HH-HH>.json    window HH-HH (3h)  (tools/mkfrag.py <date> HH-HH; also the migrated old 3h digests)
  digests/<date>/<HH-HH>.json       legacy 3h digest (before tg_migrate3to6.py moved it into 3h/)
For every 3-hour sub-range of the block, hourly fragments win if any exist; otherwise a 3h fragment is used.

Output digests/<date>/<block>.json: per group the fragments as a timeline, NEWEST HOUR FIRST
('**HH:00–HH:00**' line + that fragment's topics; topics newest first, speech lines oldest first, '~ 涉及商家' chips —
see tools/order.py); fragments that are 无重要内容 are skipped; a group
with nothing in the whole block gets 无重要内容. msg_count = sum. partial = true until every hour of the
block is covered by a non-partial fragment.
"""
import argparse, glob, json, os, re, subprocess, sys
from datetime import datetime, timedelta, timezone
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, 'tools'))
from order import order_content   # newest-first hours/topics, oldest-first speech lines, 涉及商家 chips
TZ = timezone(timedelta(hours=8))
BLOCKS = [(0, 6), (6, 12), (12, 18), (18, 24)]
NIL = re.compile(r'^\s*无重要内容\s*$')

def lbl(h1, h2): return f'{h1:02d}-{h2:02d}'

def ddir(date): return os.path.join(BASE, 'digests', date)

def load(path):
    d = json.load(open(path)); h1, h2 = (int(x) for x in d['window'].split('-'))
    return {'h1': h1, 'h2': h2, 'path': path, 'doc': d, 'partial': bool(d.get('partial'))}

def fragments(date, b1, b2):
    """Fragments covering block [b1,b2) in time order."""
    out = []
    for s in range(b1, b2, 3):
        hourly = [load(p) for h in range(s, s + 3) for p in [os.path.join(ddir(date), 'hourly', f'{h:02d}.json')] if os.path.exists(p)]
        if hourly: out += hourly; continue
        for p in (os.path.join(ddir(date), '3h', lbl(s, s + 3) + '.json'), os.path.join(ddir(date), lbl(s, s + 3) + '.json')):
            if os.path.exists(p): out.append(load(p)); break
    return sorted(out, key=lambda f: f['h1'])

def hm(date, h): return (datetime.strptime(date, '%Y-%m-%d') + timedelta(hours=h)).strftime('%Y-%m-%d %H:%M')

def merge(date, b1, b2):
    frags = fragments(date, b1, b2)
    if not frags: return None, []
    groups = json.load(open(os.path.join(BASE, 'groups.json')))
    groups = sorted(groups, key=lambda g: g.get('order') or 999)
    order = [g['key'] for g in groups]; titles = {g['key']: g['title'] for g in groups}
    for f in frags:                                   # keep groups that appear only in fragments too
        for it in f['doc']['items']:
            if it['group'] not in order: order.append(it['group']); titles[it['group']] = it.get('title') or it['group']
    covered = set(); partial_frag = False
    for f in frags:
        covered.update(range(f['h1'], f['h2'])); partial_frag = partial_frag or f['partial']
    missing = [h for h in range(b1, b2) if h not in covered]
    items = []
    for k in order:
        if not any(x['group'] == k for f in frags for x in f['doc']['items']):
            continue                                  # group not tracked yet in these hours (added to groups.json later)
        parts, verify, total, title = [], [], 0, titles[k]
        for f in frags:
            it = next((x for x in f['doc']['items'] if x['group'] == k), None)
            if not it: continue
            total += it.get('msg_count') or 0; title = it.get('title') or title
            end = f"{f['h2']:02d}:00" if not f['partial'] else (f['doc'].get('win_end') or '')[11:16] or f"{f['h2']:02d}:00"
            for vl in (it.get('verify') or '').strip().split('\n'):
                vl = vl.strip()
                if not vl: continue
                vl = re.sub(r'^[-*•]\s*', '', vl)
                verify.append(f"- （{f['h1']:02d}:00–{end}）{vl}")
            c = (it.get('content') or '').strip()
            if not c or NIL.match(c): continue
            parts.append(f"**{f['h1']:02d}:00–{end}**\n{c}")
        content = '\n\n'.join(reversed(parts)) or '无重要内容'          # newest hour first
        if verify:
            content += '\n\n#### 🔎 网上核验（外部公开来源，不是群友发言）\n' + '\n'.join(verify)
        items.append({'group': k, 'title': title, 'msg_count': total, 'content': order_content(content)})
    last = frags[-1]
    win_end = last['doc'].get('win_end') if last['partial'] else hm(date, last['h2'])
    doc = {'date': date, 'window': lbl(b1, b2), 'partial': bool(missing) or partial_frag,
           'win_start': hm(date, b1), 'win_end': win_end, 'items': items,
           'sources': [os.path.relpath(f['path'], BASE) for f in frags]}
    return doc, missing

def attach_images(path):
    """Add item['images'] from captured photos (tools/attach_images.py; content text untouched)."""
    r = subprocess.run([sys.executable, os.path.join(BASE, 'tools', 'attach_images.py'), path], capture_output=True, text=True)
    print((r.stdout or r.stderr).strip())

def push(path):
    subprocess.run([sys.executable, os.path.join(BASE, 'tg_digest_push.py'), path], check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date'); ap.add_argument('--block', help='00-06 | 06-12 | 12-18 | 18-24 | lasthour')
    ap.add_argument('--all', action='store_true'); ap.add_argument('--push', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    now = datetime.now(TZ)
    if a.block == 'lasthour':
        h = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
        date = h.strftime('%Y-%m-%d'); blocks = [b for b in BLOCKS if b[0] <= h.hour < b[1]]
    else:
        date = a.date or now.strftime('%Y-%m-%d')
        if a.all: blocks = BLOCKS
        elif a.block: blocks = [tuple(int(x) for x in a.block.split('-'))]
        else: ap.error('need --block or --all')
    for b in blocks:
        if b not in BLOCKS: sys.exit(f'bad block {b}')
        doc, missing = merge(date, *b)
        if doc is None:
            if not a.all: print(f'{date} {lbl(*b)}: no fragments')
            continue
        path = os.path.join(ddir(date), lbl(*b) + '.json')
        info = (f"{date} {lbl(*b)} partial={doc['partial']} until {doc['win_end'][11:]} "
                f"missing_hours={missing} sources={len(doc['sources'])} "
                + ' '.join(f"{i['group']}={i['msg_count']}" for i in doc['items']))
        if a.dry_run:
            print('[dry-run]', info); print(json.dumps(doc, ensure_ascii=False, indent=1)[:4000]); continue
        os.makedirs(ddir(date), exist_ok=True)
        json.dump(doc, open(path, 'w'), ensure_ascii=False, indent=1)
        print(path, info)
        attach_images(path)
        if a.push: push(path)

if __name__ == '__main__':
    main()
