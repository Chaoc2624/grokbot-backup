#!/usr/bin/env python3
"""Board API client for the bookmark brief routine.
  board_client.py carryover            -> JSON list of open items to re-push (not low / snoozed / ads)
  board_client.py ids                  -> JSON list of every item id already on the board
  board_client.py ingest payload.json  -> payload = {"label": "...", "items": [new items with category], "carried_ids": [...]}
  board_client.py brief payload.json   -> payload = {"label": "2026-10-08 中午", "run_at": "2026-10-08 12:00", "summary": "...",
                                          "new_ids": [...], "carried_ids": [...], "pdf_path": "/workspace/xbm/x.pdf" (optional)}
                                          upserts the timeline entry with the same label (ingest already creates it)
  board_client.py radar payload.json   -> payload = {"label","run_at","window_start","window_end","empty",
                                          "items":[{"name","desc","source","url","first_seen",
                                                    "keyword_rank"?, "keyword"?, "reason"?}], "keywords":[{"keyword","reason"}]}  (upsert by label)
                                          optional per-item keyword_rank/keyword/reason mark that product as a picked 建站词
                                          (highlighted at the top of the 新词 table with 「建议：reason」); see /workspace/xbm/RADAR_NOTE.md
  board_client.py radar-delete LABEL   -> remove a radar run
Uses https://x.omnitools.cc, falls back to ssh root@192.255.151.85 -> 127.0.0.1:10091."""
import sys, base64, json, os, subprocess, urllib.request
env = dict(l.strip().split('=', 1) for l in open(os.path.expanduser('~/.xbm/board.env')) if '=' in l)
TOK = env['XBM_API_TOKEN']
def call(path, data=None, method=None):
    body = json.dumps(data, ensure_ascii=False).encode() if data is not None else None
    try:
        r = urllib.request.Request('https://x.omnitools.cc' + path, data=body, method=method, headers={'Authorization': 'Bearer ' + TOK, 'Content-Type': 'application/json', 'User-Agent': 'xbm-client'})
        return json.load(urllib.request.urlopen(r, timeout=20))
    except Exception:
        cmd = ['ssh', '-o', 'ConnectTimeout=10', '-o', 'BatchMode=yes', '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=3', 'root@192.255.151.85', f"curl -sf --max-time 30 {'-X ' + method + ' ' if method else ''}-H 'Authorization: Bearer {TOK}' -H 'Content-Type: application/json' " + ("--data-binary @- " if body else "") + f"http://127.0.0.1:10091{path}"]
        return json.loads(subprocess.run(cmd, input=body, capture_output=True, check=True, timeout=60).stdout)
if __name__ == '__main__':
    c = sys.argv[1]
    if c == 'carryover': print(json.dumps(call('/api/agent/carryover')['items'], ensure_ascii=False, indent=1))
    elif c == 'ids': print(json.dumps(call('/api/agent/ids')['ids']))
    elif c == 'ingest': print(json.dumps(call('/api/agent/ingest', json.load(open(sys.argv[2]))), ensure_ascii=False))
    elif c == 'brief':
        p = json.load(open(sys.argv[2])); pdf = p.pop('pdf_path', None)
        if pdf: p['pdf_base64'] = base64.b64encode(open(pdf, 'rb').read()).decode()
        print(json.dumps(call('/api/agent/brief', p), ensure_ascii=False))
    elif c == 'radar': print(json.dumps(call('/api/agent/radar', json.load(open(sys.argv[2]))), ensure_ascii=False))
    elif c == 'radar-delete':
        from urllib.parse import quote
        print(json.dumps(call('/api/agent/radar?label=' + quote(sys.argv[2]), method='DELETE')))
