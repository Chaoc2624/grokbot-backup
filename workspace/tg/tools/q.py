#!/usr/bin/env python3
"""q.py WIN REGEX [GROUPKEY] [--date D] [--n N] [--ctx K] [--count]
grep fetched messages for fact-checking. WIN = 'hourly/19' or a 3h label like '18-21'.
--count: per group, number of matching messages and distinct people (bots excluded) = 热度 for that topic.
regex is case-insensitive."""
import json, re, sys, argparse, datetime, os
sys.path.insert(0, '/workspace/tg')
from tg_topics import is_bot
ap = argparse.ArgumentParser(); ap.add_argument('win'); ap.add_argument('rx'); ap.add_argument('grp', nargs='?')
ap.add_argument('--n', type=int, default=30); ap.add_argument('--ctx', type=int, default=0)
ap.add_argument('--date', default=datetime.date.today().isoformat()); ap.add_argument('--w', type=int, default=220)
ap.add_argument('--count', action='store_true')
a = ap.parse_args()
d = json.load(open(f'/workspace/tg/data/{a.date}/{a.win}.json'))
rx = re.compile(a.rx, re.I); n = 0
for g in d['groups']:
    if a.grp and g['key'] != a.grp: continue
    ms = sorted(g['messages'], key=lambda m: m['time'])
    if a.count:
        hit = [m for m in ms if rx.search(m.get('text') or '') and not is_bot(m)]
        if hit: print(f"{g['key']}: {len(hit)} 条 / {len({m.get('sender') for m in hit})} 人  ({', '.join(sorted({m.get('sender') or '?' for m in hit})[:8])})")
        continue
    for i, m in enumerate(ms):
        if rx.search((m.get('text') or '') + ' ' + (m.get('sender') or '')):
            for j in range(max(0, i - a.ctx), min(len(ms), i + a.ctx + 1)):
                x = ms[j]; t = (x.get('text') or '').replace('\n', ' ⏎ ')
                print(('>' if j == i else ' '), g['key'], x['time'][11:16], x.get('sender'), ':', t[:a.w], '<%s>' % x['id'], ('↩' + str(x['reply_to'])) if x.get('reply_to') else '')
            if a.ctx: print('--')
            n += 1
            if n >= a.n: sys.exit()
