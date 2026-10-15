#!/usr/bin/env python3
"""Upsert TG group digests to the board (💬 TG 群总结).

  tg_digest_push.py digests/2026-10-08/18-21.json [more.json ...]
  tg_digest_push.py --date 2026-10-08            # push every digests/2026-10-08/*.json
  tg_digest_push.py --delete 2026-10-08 [--window 18-21]

Digest file format:
  {"date": "2026-10-08", "window": "18-21" | "daily", "partial": false,
   "win_start": "2026-10-08 18:00", "win_end": "2026-10-08 21:00",
   "items": [{"group": "all" | "<group key>", "title": "群名", "content": "markdown", "msg_count": 123}, ...]}
Each push replaces that (date, window) on the board (groups not in items are removed).
Uses https://xbm.omnitools.cc with the token from ~/.xbm/board.env; falls back to ssh to the
RackNerd box -> 127.0.0.1:10091 if the public URL fails.
"""
import sys, os, json, glob, argparse, subprocess, urllib.request
from urllib.parse import quote
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, 'tools'))
from order import order_doc   # enforce ordering + 涉及商家 chips on every push (file is rewritten to match)
env = dict(l.strip().split('=', 1) for l in open(os.path.expanduser('~/.xbm/board.env')) if '=' in l)
TOK = env['XBM_API_TOKEN']

def call(path, data=None, method=None):
    body = json.dumps(data, ensure_ascii=False).encode() if data is not None else None
    try:
        r = urllib.request.Request('https://xbm.omnitools.cc' + path, data=body, method=method,
                                   headers={'Authorization': 'Bearer ' + TOK, 'Content-Type': 'application/json', 'User-Agent': 'xbm-client'})
        return json.load(urllib.request.urlopen(r, timeout=30))
    except urllib.error.HTTPError as e:
        if e.code in (400, 401): raise SystemExit(f'board rejected {path}: {e.code} {e.read()[:300]!r}')
        err = e
    except Exception as e:
        err = e
    print(f'public URL failed ({err}); using ssh fallback', file=sys.stderr)
    cmd = ['ssh', '-o', 'ConnectTimeout=10', 'root@192.255.151.85',
           f"curl -sf {'-X ' + method + ' ' if method else ''}-H 'Authorization: Bearer {TOK}' -H 'Content-Type: application/json' "
           + ("--data-binary @- " if body else "") + f"'http://127.0.0.1:10091{path}'"]
    return json.loads(subprocess.run(cmd, input=body, capture_output=True, check=True).stdout)

def push(path):
    d = json.load(open(path))
    if order_doc(d):
        json.dump(d, open(path, 'w'), ensure_ascii=False, indent=1)
    d['replace'] = True
    for it in d.get('items', []):
        if not str(it.get('content') or '').strip(): it['content'] = '无重要内容'
    r = call('/api/agent/tg', d)
    print(path, '->', json.dumps(r, ensure_ascii=False))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='*'); ap.add_argument('--date'); ap.add_argument('--delete'); ap.add_argument('--window')
    a = ap.parse_args()
    if a.delete:
        q = '/api/agent/tg?date=' + quote(a.delete) + ('&window=' + quote(a.window) if a.window else '')
        print(call(q, method='DELETE')); sys.exit()
    files = list(a.files)
    if a.date: files += sorted(glob.glob(os.path.join(BASE, 'digests', a.date, '*.json')))
    if not files: ap.error('no digest files')
    for f in files: push(f)
