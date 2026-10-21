#!/usr/bin/env python3
"""Per-date image index for halo-board. Source (authoritative): /workspace/tg/digests/<date>/hourly/<HH>.json and
<date>/<00-06|06-12|12-18|18-24>.json items[].images. Only image metadata + `line` is written (no summary content)."""
import json, os, glob, sys
ROOT = '/workspace/tg'; OUT = os.path.join(ROOT, 'board_sync/out/index')
os.makedirs(OUT, exist_ok=True)
FIELDS = ('path', 'thumb', 'w', 'h', 'msg_id', 'chat', 'time', 'sender', 'link', 'line')
days = sys.argv[1:] or sorted(d for d in os.listdir(os.path.join(ROOT, 'digests')) if d[:2] == '20')[-3:]
for d in days:
    base = os.path.join(ROOT, 'digests', d)
    files = sorted(glob.glob(os.path.join(base, 'hourly', '[0-9][0-9].json'))) + [os.path.join(base, f'{w}.json') for w in ('00-06', '06-12', '12-18', '18-24')]
    imgs = {}
    for f in files:
        if not os.path.exists(f): continue
        try: doc = json.load(open(f))
        except Exception: continue
        src = 'hourly' if '/hourly/' in f else '6h'
        for it in doc.get('items') or []:
            for im in it.get('images') or []:
                if not im.get('path'): continue
                rec = {k: im.get(k) for k in FIELDS}
                rec['chat'] = rec['chat'] or it.get('group'); rec['group'] = it.get('group'); rec['title'] = it.get('title')
                rec['line'] = rec['line'].strip() if isinstance(rec['line'], str) else None
                k = f"{rec['chat']}:{rec['msg_id']}"
                old = imgs.get(k)
                # prefer an entry with a line; prefer hourly over 6h
                if old is None or (old['line'] is None and rec['line'] is not None) or (old['line'] is None and rec['line'] is None and src == 'hourly'):
                    imgs[k] = rec
    out = os.path.join(OUT, f'{d}.json'); tmp = out + '.tmp'
    json.dump({'date': d, 'images': sorted(imgs.values(), key=lambda x: x['time'] or '')}, open(tmp, 'w'), ensure_ascii=False)
    os.replace(tmp, out); print(d, len(imgs))
