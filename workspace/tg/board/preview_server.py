#!/usr/bin/env python3
"""Local preview of the board TG tab: serves board/index.html; /api/tg = live API data with today's
content replaced by the local digests (so new formats can be checked before pushing)."""
import json, os, sys, glob, http.server
BASE = '/workspace/tg'; sys.path.insert(0, BASE); sys.argv = sys.argv[:1]
import tg_digest_push as P
DATE = os.environ.get('PDATE', '2026-10-08'); LOCAL = os.environ.get('LOCAL', '1') == '1'
HTML = os.environ.get('HTML', os.path.join(BASE, 'board', 'index.html'))
def tgdata(qs):
    r = P.call('/api/tg' + qs)
    if not LOCAL: return r
    for day in r['days']:
        if day['date'] != DATE: continue
        dd = json.load(open(f'{BASE}/digests/{DATE}/daily.json')); it = dd['items'][0]
        day['daily'].update(content=it['content'], msg_count=it['msg_count'], win_end=dd['win_end'])
        wins = []
        for f in sorted(glob.glob(f'{BASE}/digests/{DATE}/[0-9][0-9]-[0-9][0-9].json')):
            b = json.load(open(f))
            gs = [{'win': b['window'], 'grp': i['group'], 'title': i['title'], 'content': i['content'], 'msg_count': i['msg_count'],
                   'partial': int(b['partial']), 'win_start': b['win_start'], 'win_end': b['win_end'], 'rank': k} for k, i in enumerate(b['items'])]
            wins.append({'window': b['window'], 'partial': b['partial'], 'all': None, 'groups': gs, 'msg_count': sum(g['msg_count'] for g in gs),
                         'win_start': b['win_start'], 'win_end': b['win_end'], 'updated_at': ''})
        day['windows'] = wins
    return r
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send(self, code, body, ct='application/json'):
        b = body.encode() if isinstance(body, str) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code); self.send_header('Content-Type', ct + '; charset=utf-8'); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        p, _, q = self.path.partition('?')
        if p == '/': return self.send(200, open(HTML, encoding='utf-8').read(), 'text/html')
        if p == '/api/items': return self.send(200, {'items': [], 'counts': json.load(open(f'{BASE}/board/counts.json')), 'today': DATE})
        if p == '/api/tg': return self.send(200, tgdata('?' + q))
        if p == '/api/version': return self.send(200, {'v': 'preview'})
        if p == '/api/tg/login': return self.send(200, {'state': 'authorized'})
        if p == '/api/tg/raw': return self.send(200, {'days': [], 'pulls': [], 'total': 0})
        self.send(404, {'error': 'nf'})
http.server.ThreadingHTTPServer(('127.0.0.1', int(os.environ.get('PORT', 8765))), H).serve_forever()
