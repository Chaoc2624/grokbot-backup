#!/usr/bin/env python3
"""Plan for the hourly TG run: which hour to do, its 6h block, and anything left undone in the last 24 h.

  tg_hourly.py            # prints DATE HOUR BLOCK of the last completed hour + exact commands + backlog
  tg_hourly.py --json     # same as JSON
Backlog = hours in the last 24 h whose raw data or digest fragment is missing (fetch with
`tg_fetch.py --date D --hours H-(H+1)`, then write the fragment and re-merge that block).
"""
import json, os, sys
from datetime import datetime, timedelta, timezone
BASE = os.path.dirname(os.path.abspath(__file__)); TZ = timezone(timedelta(hours=8))
START = '2026-10-08'   # first day of the hourly pipeline; no backlog before this
now = datetime.now(TZ); last = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
def blk(h): b = h - h % 6; return f'{b:02d}-{b + 6:02d}'
def covered(d, h):
    if os.path.exists(f'{BASE}/digests/{d}/hourly/{h:02d}.json'): return True
    s = h - h % 3; return os.path.exists(f'{BASE}/digests/{d}/3h/{s:02d}-{s + 3:02d}.json')
D, H = last.strftime('%Y-%m-%d'), last.hour
backlog = []
for i in range(1, 25):
    t = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=i); d, h = t.strftime('%Y-%m-%d'), t.hour
    if (d, h) == (D, H) or d < START: continue
    if not covered(d, h):
        backlog.append({'date': d, 'hour': h, 'block': blk(h),
                        'has_data': os.path.exists(f'{BASE}/data/{d}/hourly/{h:02d}.json')})
plan = {'date': D, 'hour': H, 'block': blk(H), 'block_final': H % 6 == 5, 'day_final': H == 23, 'backlog': backlog,
        'commands': [
            './venv/bin/python tg_fetch.py --window lasthour',
            f'./venv/bin/python tg_prep.py data/{D}/hourly/{H:02d}.json > data/{D}/hourly/{H:02d}.txt',
            f'# write specs/{D}-{H:02d}.spec from data/{D}/hourly/{H:02d}.txt per SUMMARY_RULES.md (heat via tools/q.py hourly/{H:02d} RX GROUP --count --date {D});',
            '# web-verify 3-5 key claims -> "--- 核验" lines in the group blocks',
            f'./venv/bin/python tools/checkquotes.py {D} {H:02d} specs/{D}-{H:02d}.spec',
            f'./venv/bin/python tools/mkfrag.py {D} {H:02d} < specs/{D}-{H:02d}.spec',
            f'./venv/bin/python tools/attach_images.py digests/{D}/hourly/{H:02d}.json',
            f'./venv/bin/python tg_merge6h.py --date {D} --block {blk(H)}   # NO --push; also attaches images',
            f'# update digests/{D}/daily.json (partial={str(H != 23).lower()}, win_end={(last + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")})',
            f'./venv/bin/python tools/attach_images.py digests/{D}/daily.json']}   # never push to the board
if '--json' in sys.argv: print(json.dumps(plan, ensure_ascii=False, indent=1)); sys.exit()
print(f"last completed hour: {D} {H:02d}:00-{H + 1:02d}:00  block {plan['block']}"
      + ('  (block completes)' if plan['block_final'] else '') + ('  (day completes -> finalise daily)' if plan['day_final'] else ''))
for c in plan['commands']: print('  ' + c)
print('backlog:', ', '.join(f"{b['date']} {b['hour']:02d}" + ('' if b['has_data'] else '(no data)') for b in backlog) or 'none')
