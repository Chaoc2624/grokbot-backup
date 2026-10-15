#!/usr/bin/env python3
"""X 书签待办看板 — stdlib only (http.server + sqlite3).
Env: XBM_DB, XBM_PASSWORD, XBM_API_TOKEN, XBM_SECRET, XBM_PORT"""
import os, base64, json, sqlite3, hmac, hashlib, time, re, html, datetime as dt
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from http.cookies import SimpleCookie

DB = os.environ.get('XBM_DB', '/opt/xbm-board/board.db')
PASSWORD = os.environ['XBM_PASSWORD']
API_TOKEN = os.environ['XBM_API_TOKEN']
SECRET = os.environ['XBM_SECRET'].encode()
PORT = int(os.environ.get('XBM_PORT', '10091'))
BASE = os.environ.get('XBM_BASE', '').rstrip('/')
PUBLIC = os.environ.get('XBM_PUBLIC', 'https://xbm.omnitools.cc')
TZ = dt.timezone(dt.timedelta(hours=8))
CATS = ('urgent', 'related', 'needs', 'ads')
STATUSES = ('open', 'done', 'ignored')
PRIOS = ('urgent', 'normal', 'low')

def now(): return dt.datetime.now(TZ).strftime('%Y-%m-%d %H:%M')
def today(): return dt.datetime.now(TZ).strftime('%Y-%m-%d')

def db():
    c = sqlite3.connect(DB, timeout=10); c.row_factory = sqlite3.Row
    c.execute('PRAGMA journal_mode=WAL'); return c

def init():
    with db() as c:
        cols = {r[1] for r in c.execute('PRAGMA table_info(items)')}
        if cols and 'posted_at' not in cols:
            c.execute('ALTER TABLE items ADD COLUMN posted_at TEXT')
        if cols and 'read_at' not in cols:
            c.execute('ALTER TABLE items ADD COLUMN read_at TEXT')
        c.executescript('''
        CREATE TABLE IF NOT EXISTS items(
          id TEXT PRIMARY KEY, url TEXT, title TEXT, tag TEXT, need TEXT, action TEXT,
          deadline TEXT, due_date TEXT, category TEXT, priority TEXT, status TEXT DEFAULT 'open',
          snooze_until TEXT, note TEXT DEFAULT '', posted_at TEXT, read_at TEXT, first_seen TEXT, last_pushed TEXT,
          push_count INTEGER DEFAULT 0, updated_at TEXT, closed_at TEXT);
        CREATE TABLE IF NOT EXISTS _migrate(v INTEGER);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, item_id TEXT, ts TEXT, what TEXT);
        CREATE TABLE IF NOT EXISTS briefs(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, label TEXT, new_count INTEGER, carried_count INTEGER);
        CREATE TABLE IF NOT EXISTS brief_items(brief_id INTEGER, item_id TEXT, kind TEXT, PRIMARY KEY(brief_id,item_id));
        ''')
        bcols = {r[1] for r in c.execute('PRAGMA table_info(briefs)')}
        for col in ('run_at', 'summary', 'pdf_path'):
            if col not in bcols: c.execute(f'ALTER TABLE briefs ADD COLUMN {col} TEXT')

        c.executescript('''
        CREATE TABLE IF NOT EXISTS radar_runs(id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT UNIQUE, run_at TEXT, window_start TEXT, window_end TEXT, empty INTEGER DEFAULT 0, note TEXT);
        CREATE TABLE IF NOT EXISTS radar_items(id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INTEGER, name TEXT, "desc" TEXT, source TEXT, url TEXT, first_seen TEXT);
        CREATE TABLE IF NOT EXISTS radar_keywords(id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INTEGER, keyword TEXT, reason TEXT, rank INTEGER);
        CREATE TABLE IF NOT EXISTS tg_digests(id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL, win TEXT NOT NULL, grp TEXT NOT NULL,
          title TEXT, content TEXT, msg_count INTEGER, partial INTEGER DEFAULT 0, win_start TEXT, win_end TEXT, rank INTEGER DEFAULT 0,
          created_at TEXT, updated_at TEXT, UNIQUE(date, win, grp));
        CREATE INDEX IF NOT EXISTS tg_digests_date ON tg_digests(date);
        ''')
        rcols = {r[1] for r in c.execute('PRAGMA table_info(radar_items)')}
        for col, typ in (('keyword', 'TEXT'), ('kw_reason', 'TEXT'), ('kw_rank', 'INTEGER')):
            if col not in rcols: c.execute(f'ALTER TABLE radar_items ADD COLUMN {col} {typ}')

def post_radar(b):
    """b = {label, run_at, window_start, window_end, empty, note?,
            items:[{name,desc,source,url,first_seen, keyword?, reason?, keyword_rank?}], keywords:[{keyword,reason}]}; upsert by label.
       Optional per-item keyword fields mark that product as a picked 建站词 (shown highlighted at the top of the table);
       a per-item keyword not already in `keywords` is added there too (so 热词榜 counts it)."""
    label = str(b.get('label') or '').strip()
    if not label: raise ValueError('label')
    items = b.get('items') or []; kws = b.get('keywords') or []
    if not isinstance(items, list) or not isinstance(kws, list): raise ValueError('items/keywords')
    empty = 1 if b.get('empty') or not items else 0
    with db() as c:
        r = c.execute('SELECT id FROM radar_runs WHERE label=?', (label,)).fetchone()
        vals = (b.get('run_at') or now(), b.get('window_start'), b.get('window_end'), empty, b.get('note'))
        if r:
            rid = r[0]; c.execute('UPDATE radar_runs SET run_at=?,window_start=?,window_end=?,empty=?,note=? WHERE id=?', vals + (rid,))
            c.execute('DELETE FROM radar_items WHERE run_id=?', (rid,)); c.execute('DELETE FROM radar_keywords WHERE run_id=?', (rid,))
        else:
            rid = c.execute('INSERT INTO radar_runs(run_at,window_start,window_end,empty,note,label) VALUES(?,?,?,?,?,?)', vals + (label,)).lastrowid
        kws = [({'keyword': k} if isinstance(k, str) else k) for k in kws]
        have = {re.sub(r'\W+', '', str(k.get('keyword', ''))).lower() for k in kws}
        for it in items:
            kr = it.get('keyword_rank')
            try: kr = int(kr) if kr not in (None, '') else None
            except (TypeError, ValueError): kr = None
            kw = str(it.get('keyword') or '').strip()[:100] or None
            if kr is not None and not kw: kw = str(it.get('name', '')).strip()[:100] or None
            rs = str(it.get('reason') or '')[:500] or None
            c.execute('INSERT INTO radar_items(run_id,name,"desc",source,url,first_seen,keyword,kw_reason,kw_rank) VALUES(?,?,?,?,?,?,?,?,?)',
                      (rid, str(it.get('name', ''))[:200], str(it.get('desc', ''))[:500], str(it.get('source', ''))[:100], str(it.get('url', ''))[:500], it.get('first_seen'), kw, rs, kr))
            if kw and re.sub(r'\W+', '', kw).lower() not in have:
                have.add(re.sub(r'\W+', '', kw).lower()); kws.append({'keyword': kw, 'reason': rs or '', 'rank': kr or len(kws) + 1})
        for n, k in enumerate(kws[:10], 1):
            c.execute('INSERT INTO radar_keywords(run_id,keyword,reason,rank) VALUES(?,?,?,?)', (rid, str(k.get('keyword', '')).strip()[:100], str(k.get('reason', ''))[:500], k.get('rank') or n))
    return {'id': rid, 'items': len(items), 'keywords': len(kws[:10]), 'empty': bool(empty)}

def delete_radar(label):
    with db() as c:
        r = c.execute('SELECT id FROM radar_runs WHERE label=?', (label,)).fetchone()
        if not r: return False
        for t in ('radar_items', 'radar_keywords'): c.execute(f'DELETE FROM {t} WHERE run_id=?', (r[0],))
        c.execute('DELETE FROM radar_runs WHERE id=?', (r[0],))
    return True

def run_day(r):
    m = re.search(r'\d{4}-\d{2}-\d{2}', r.get('label') or ''); return m.group(0) if m else (r.get('run_at') or '')[:10]

def list_radar(frm=None, to=None):
    D = r'\d{4}-\d{2}-\d{2}'
    frm = frm if frm and re.fullmatch(D, frm) else None; to = to if to and re.fullmatch(D, to) else None
    with db() as c:
        runs = [dict(r) for r in c.execute('SELECT * FROM radar_runs ORDER BY run_at DESC, id DESC')]
        for r in runs: r['day'] = run_day(r)
        runs = [r for r in runs if (not frm or r['day'] >= frm) and (not to or r['day'] <= to)][:500]
        for r in runs:
            r['empty'] = bool(r['empty'])
            r['items'] = [dict(x) for x in c.execute('SELECT name,"desc",source,url,first_seen,keyword,kw_reason AS reason,kw_rank AS keyword_rank FROM radar_items WHERE run_id=? ORDER BY first_seen, id', (r['id'],))]
            r['keywords'] = [dict(x) for x in c.execute('SELECT keyword,reason,rank FROM radar_keywords WHERE run_id=? ORDER BY rank', (r['id'],))]
    return runs

# ---------- 💬 TG 群总结 ----------
D_RE = r'\d{4}-\d{2}-\d{2}'
W_RE = r'(daily|\d{2}-\d{2})'

def post_tg(b):
    """b = {date, window ('daily' | 'HH-HH'), partial?, win_start?, win_end?, replace?,
             items: [{group ('all' | key), title?, content (markdown), msg_count?}]}; upsert by (date, window, group).
       content speech lines '> 名：原话' may end with an optional time token '{{YYYY-MM-DD HH:MM:SS}}' (or '{{…~HH:MM:SS}}');
       the page shows it on hover at the row's right end. Lines without it render as before.
       replace=true removes groups of that date/window not present in items."""
    date = str(b.get('date') or ''); win = str(b.get('window') or '')
    if not re.fullmatch(D_RE, date): raise ValueError('date')
    if not re.fullmatch(W_RE, win): raise ValueError('window')
    items = b.get('items')
    if items is None and 'content' in b: items = [b]
    if not isinstance(items, list) or not items: raise ValueError('items')
    ts = now(); n = 0
    with db() as c:
        keep = []
        for rank, it in enumerate(items):
            g = str(it.get('group') or 'all')[:64]; keep.append(g)
            vals = (str(it.get('title') or ('全部群' if g == 'all' else g))[:200], str(it.get('content') or '')[:200000],
                    it.get('msg_count'), 1 if b.get('partial') else 0, b.get('win_start'), b.get('win_end'), rank, ts)
            r = c.execute('SELECT id FROM tg_digests WHERE date=? AND win=? AND grp=?', (date, win, g)).fetchone()
            if r: c.execute('UPDATE tg_digests SET title=?,content=?,msg_count=?,partial=?,win_start=?,win_end=?,rank=?,updated_at=? WHERE id=?', vals + (r[0],))
            else: c.execute('INSERT INTO tg_digests(title,content,msg_count,partial,win_start,win_end,rank,updated_at,created_at,date,win,grp) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)', vals + (ts, date, win, g))
            n += 1
        if b.get('replace'):
            c.execute(f'DELETE FROM tg_digests WHERE date=? AND win=? AND grp NOT IN ({",".join("?" * len(keep))})', [date, win] + keep)
    return {'date': date, 'window': win, 'upserted': n}

def delete_tg(date, win=None):
    with db() as c:
        if win: return c.execute('DELETE FROM tg_digests WHERE date=? AND win=?', (date, win)).rowcount
        return c.execute('DELETE FROM tg_digests WHERE date=?', (date,)).rowcount

def list_tg(frm=None, to=None, page=0, per=5):
    frm = frm if frm and re.fullmatch(D_RE, frm) else None; to = to if to and re.fullmatch(D_RE, to) else None
    with db() as c:
        alldays = [r[0] for r in c.execute('SELECT DISTINCT date FROM tg_digests ORDER BY date DESC')]
        days = [d for d in alldays if (not frm or d >= frm) and (not to or d <= to)]
        total = len(days); days = days[page * per:(page + 1) * per] if per else days
        out = []
        for d in days:
            rows = [dict(r) for r in c.execute('SELECT win,grp,title,content,msg_count,partial,win_start,win_end,rank,created_at,updated_at FROM tg_digests WHERE date=? ORDER BY rank, id', (d,))]
            daily = [r for r in rows if r['win'] == 'daily']
            wins = {}
            for r in rows:
                if r['win'] == 'daily': continue
                w = wins.setdefault(r['win'], {'window': r['win'], 'partial': False, 'all': None, 'groups': [], 'msg_count': 0,
                                               'win_start': r['win_start'], 'win_end': r['win_end'], 'updated_at': r['updated_at']})
                w['partial'] = w['partial'] or bool(r['partial']); w['updated_at'] = max(w['updated_at'] or '', r['updated_at'] or '')
                if r['grp'] == 'all': w['all'] = r
                else: w['groups'].append(r); w['msg_count'] += r['msg_count'] or 0
            out.append({'date': d,
                        'daily': next((r for r in daily if r['grp'] == 'all'), None),
                        'daily_groups': [r for r in daily if r['grp'] != 'all'],
                        'windows': sorted(wins.values(), key=lambda w: w['window'])})
    return {'days': out, 'all_days': alldays, 'total_days': total, 'page': page, 'per': per, 'today': today()}

PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(DB)), 'pdfs')

def map_brief(c, bid, ids, kind):
    for iid in ids:
        c.execute('INSERT OR REPLACE INTO brief_items(brief_id,item_id,kind) VALUES(?,?,?)', (bid, str(iid), kind))

def post_brief(b):
    """b = {label, run_at?, summary?, new_ids?, carried_ids?, pdf_base64?}; upserts by label."""
    label = str(b.get('label') or '').strip()
    if not label: raise ValueError('label')
    run_at = b.get('run_at') or now()
    with db() as c:
        r = c.execute('SELECT id FROM briefs WHERE label=? ORDER BY id DESC LIMIT 1', (label,)).fetchone()
        if r: bid = r[0]
        else: bid = c.execute('INSERT INTO briefs(ts,label,new_count,carried_count) VALUES(?,?,0,0)', (run_at, label)).lastrowid
        if 'new_ids' in b: c.execute("DELETE FROM brief_items WHERE brief_id=? AND kind='new'", (bid,)); map_brief(c, bid, b['new_ids'], 'new')
        if 'carried_ids' in b: c.execute("DELETE FROM brief_items WHERE brief_id=? AND kind='carried'", (bid,)); map_brief(c, bid, b['carried_ids'], 'carried')
        pdf = None
        if b.get('pdf_base64'):
            os.makedirs(PDF_DIR, exist_ok=True); pdf = os.path.join(PDF_DIR, f'{bid}.pdf')
            with open(pdf, 'wb') as f: f.write(base64.b64decode(b['pdf_base64']))
        nn = c.execute("SELECT COUNT(*) FROM brief_items WHERE brief_id=? AND kind='new'", (bid,)).fetchone()[0]
        nc = c.execute("SELECT COUNT(*) FROM brief_items WHERE brief_id=? AND kind='carried'", (bid,)).fetchone()[0]
        c.execute('UPDATE briefs SET run_at=?, summary=COALESCE(?,summary), pdf_path=COALESCE(?,pdf_path), new_count=?, carried_count=? WHERE id=?',
                  (run_at, b.get('summary'), pdf, nn, nc, bid))
    return {'id': bid, 'new': nn, 'carried': nc, 'pdf': bool(pdf)}

def list_briefs():
    with db() as c:
        bs = [dict(r) for r in c.execute('SELECT id,label,COALESCE(run_at,ts) run_at,summary,pdf_path IS NOT NULL has_pdf,new_count,carried_count FROM briefs ORDER BY COALESCE(run_at,ts) DESC, id DESC')]
        for b in bs:
            rows = c.execute('''SELECT bi.kind, i.id, i.title, i.tag, i.url, i.posted_at, i.status, i.priority, i.read_at FROM brief_items bi
                JOIN items i ON i.id=bi.item_id WHERE bi.brief_id=? ORDER BY CASE i.priority WHEN 'urgent' THEN 0 ELSE 1 END, i.first_seen''', (b['id'],))
            b['new'] = []; b['carried'] = []
            for r in rows: d = dict(r); b[d.pop('kind')].append(d)
    return bs

def brief_pdf(bid):
    with db() as c: r = c.execute('SELECT pdf_path,label FROM briefs WHERE id=?', (bid,)).fetchone()
    if r and r[0] and os.path.exists(r[0]): return open(r[0], 'rb').read(), r[1]
    return None, None

def ev(c, iid, what): c.execute('INSERT INTO events(item_id,ts,what) VALUES(?,?,?)', (iid, now(), what))

def item_id(it):
    if it.get('id'): return str(it['id'])
    m = re.search(r'status/(\d+)', it.get('url', '')); return m.group(1) if m else hashlib.sha1(it.get('title', '').encode()).hexdigest()[:16]

def view_rows(view, q='', unread=False):
    t = today()
    where = {
      'urgent':  "status='open' AND priority='urgent' AND (snooze_until IS NULL OR snooze_until<=?)",
      'open':    "status='open' AND priority!='low' AND (snooze_until IS NULL OR snooze_until<=?)",
      'low':     "status='open' AND priority='low' AND ?=?",
      'snoozed': "status='open' AND snooze_until>?",
      'done':    "status='done' AND ?=?",
      'ignored': "status='ignored' AND ?=?",
      'all':     "?=?",
    }[view]
    args = [t] if where.count('?') == 1 else [1, 1]
    if unread: where += " AND read_at IS NULL"
    if q:
        where += " AND (title LIKE ? OR need LIKE ? OR action LIKE ? OR note LIKE ? OR tag LIKE ?)"; args += ['%'+q+'%']*5
    order = "CASE priority WHEN 'urgent' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END, CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date, push_count DESC, first_seen DESC"
    if view in ('done', 'ignored'): order = 'closed_at DESC'
    with db() as c:
        return [dict(r) for r in c.execute(f'SELECT * FROM items WHERE {where} ORDER BY {order}', args)]

def counts():
    out = {}
    for v in ('urgent', 'open', 'low', 'snoozed', 'done', 'ignored', 'all'):
        out[v] = len(view_rows(v)); out['unread_' + v] = len(view_rows(v, unread=True))
    return out

def sign(v): return v + '.' + hmac.new(SECRET, v.encode(), hashlib.sha256).hexdigest()[:32]
def check_sig(s):
    if not s or '.' not in s: return False
    v, _ = s.rsplit('.', 1)
    if not hmac.compare_digest(sign(v), s): return False
    try: return int(v) > time.time()
    except: return False

# ---------- carry-over rules ----------
def carryover():
    """Open items that should be re-pushed in the next brief: not low, not snoozed, not ads."""
    t = today()
    with db() as c:
        rows = [dict(r) for r in c.execute("""SELECT * FROM items WHERE status='open' AND priority!='low'
            AND category!='ads' AND (snooze_until IS NULL OR snooze_until<=?)
            ORDER BY CASE priority WHEN 'urgent' THEN 0 ELSE 1 END, due_date IS NULL, due_date, push_count DESC""", (t,))]
    for r in rows:
        r['overdue'] = bool(r['due_date'] and r['due_date'] < t)
    return rows

def ingest(body):
    """body = {label, items:[{id?,url,title,tag,need,action,deadline,due_date?,category}], carried_ids:[...]}"""
    n_new = n_upd = 0; ts = now()
    with db() as c:
        for it in body.get('items', []):
            iid = item_id(it); cat = it.get('category') if it.get('category') in CATS else 'needs'
            prio = it.get('priority') or {'urgent': 'urgent', 'ads': 'low'}.get(cat, 'normal')
            r = c.execute('SELECT id FROM items WHERE id=?', (iid,)).fetchone()
            if r:
                c.execute('UPDATE items SET last_pushed=?, push_count=push_count+1, updated_at=?, posted_at=COALESCE(posted_at,?) WHERE id=?', (ts, ts, it.get('posted_at'), iid)); n_upd += 1
            else:
                c.execute('''INSERT INTO items(id,url,title,tag,need,action,deadline,due_date,category,priority,status,posted_at,first_seen,last_pushed,push_count,updated_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,'open',?,?,?,1,?)''', (iid, it.get('url'), it.get('title'), it.get('tag'), it.get('need'), it.get('action'),
                    it.get('deadline'), it.get('due_date'), cat, prio, it.get('posted_at'), ts, ts, ts))
                ev(c, iid, f"推送入库（{body.get('label','')}）"); n_new += 1
        carried = [str(x) for x in body.get('carried_ids', [])]
        for iid in carried:
            c.execute("UPDATE items SET last_pushed=?, push_count=push_count+1 WHERE id=? AND status='open'", (ts, iid))
            # 被反复提醒仍未处理的普通事项，第3次起升为紧急
            c.execute("UPDATE items SET priority='urgent', updated_at=? WHERE id=? AND priority='normal' AND push_count>=3 AND category!='ads'", (ts, iid))
        bid = c.execute('INSERT INTO briefs(ts,run_at,label,new_count,carried_count) VALUES(?,?,?,?,?)', (ts, ts, body.get('label', ''), n_new + n_upd, len(carried))).lastrowid
        map_brief(c, bid, [item_id(it) for it in body.get('items', [])], 'new'); map_brief(c, bid, carried, 'carried')
    return {'new': n_new, 'repeated': n_upd, 'carried': len(carried)}

def update(iid, body):
    sets, args, notes = [], [], []
    ts = now()
    if body.get('status') in STATUSES:
        sets += ['status=?', 'closed_at=?']; args += [body['status'], ts if body['status'] != 'open' else None]
        notes.append({'open': '恢复为待处理', 'done': '标记完成', 'ignored': '标记忽略'}[body['status']])
        if body['status'] == 'open': sets.append('snooze_until=NULL')
    if body.get('priority') in PRIOS:
        sets.append('priority=?'); args.append(body['priority']); notes.append({'urgent': '设为紧急', 'normal': '设为普通', 'low': '降为不紧急'}[body['priority']])
    if 'snooze_days' in body:
        d = int(body['snooze_days'])
        if d > 0:
            u = (dt.datetime.now(TZ) + dt.timedelta(days=d)).strftime('%Y-%m-%d'); sets.append('snooze_until=?'); args.append(u); notes.append(f'推迟到 {u}')
        else: sets.append('snooze_until=NULL'); notes.append('取消推迟')
    if 'note' in body:
        sets.append('note=?'); args.append(str(body['note'])[:2000]); notes.append('更新备注')
    if 'due_date' in body:
        v = body['due_date'] or None
        if v and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', v): raise ValueError('due_date')
        sets.append('due_date=?'); args.append(v); notes.append(f'截止日 {v or "清除"}')
    if 'read' in body:
        sets.append('read_at=?'); args.append(ts if body['read'] else None)
        if not body['read']: notes.append('标为未读')
    if not sets: return None
    sets.append('updated_at=?'); args.append(ts)
    with db() as c:
        c.execute(f'UPDATE items SET {", ".join(sets)} WHERE id=?', args + [iid])
        for n in notes: ev(c, iid, n)
        r = c.execute('SELECT * FROM items WHERE id=?', (iid,)).fetchone()
    return dict(r) if r else None

def history(iid):
    with db() as c: return [dict(r) for r in c.execute('SELECT ts,what FROM events WHERE item_id=? ORDER BY id DESC', (iid,))]

PAGE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html'), encoding='utf-8').read()
LOGIN = '''<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Halo 的看板 · 登录</title>
<style>body{font-family:-apple-system,"PingFang SC",sans-serif;background:#f4f5f7;display:flex;height:100vh;align-items:center;justify-content:center;margin:0}
form{background:#fff;padding:28px;border-radius:12px;box-shadow:0 2px 12px #0001;width:280px}input,button{width:100%;box-sizing:border-box;padding:10px;margin-top:10px;font-size:15px;border-radius:8px;border:1px solid #ccc}
button{background:#1d6fe0;color:#fff;border:0}.e{color:#c00;font-size:13px}</style></head><body><form method=post action=login><b>Halo 的看板</b>{{E}}
<input type=password name=p placeholder=密码 autofocus><button>登录</button></form></body></html>'''

class H(BaseHTTPRequestHandler):
    server_version = 'xbm'
    def log_message(self, *a): pass
    def send(self, code, body, ctype='application/json; charset=utf-8', headers=()):
        b = body if isinstance(body, bytes) else (json.dumps(body, ensure_ascii=False) if not isinstance(body, str) else body).encode()
        self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(b)))
        self.send_header('Cache-Control', 'no-store'); self.send_header('X-Frame-Options', 'DENY')
        for k, v in headers: self.send_header(k, v)
        self.end_headers(); self.wfile.write(b)
    def body(self):
        n = int(self.headers.get('Content-Length') or 0); raw = self.rfile.read(min(n, 40_000_000)) if n else b''
        if 'json' in (self.headers.get('Content-Type') or ''): return json.loads(raw or b'{}')
        return {k: v[0] for k, v in parse_qs(raw.decode()).items()}
    def session(self):
        ck = SimpleCookie(self.headers.get('Cookie', '')); m = ck.get('xbm'); return check_sig(m.value if m else '')
    def bearer(self):
        a = self.headers.get('Authorization', ''); return a.startswith('Bearer ') and hmac.compare_digest(a[7:], API_TOKEN)
    def route(self):
        u = urlparse(self.path); p = u.path; self.base = ''
        if BASE and (p == BASE or p.startswith(BASE + '/')): p = p[len(BASE):] or '/'; self.base = BASE
        return u._replace(path=p)
    def do_GET(self):
        u = self.route(); q = parse_qs(u.query)
        if self.base and u.path == '/' and not self.path.split('?')[0].endswith('/'): return self.send(302, '', headers=[('Location', BASE + '/')])
        if u.path == '/healthz': return self.send(200, {'ok': True})
        if u.path.startswith('/api/agent/'):
            if not self.bearer(): return self.send(401, {'error': 'unauthorized'})
            if u.path == '/api/agent/carryover': return self.send(200, {'items': carryover(), 'board': PUBLIC})
            if u.path == '/api/agent/ids':
                with db() as c: return self.send(200, {'ids': [r[0] for r in c.execute('SELECT id FROM items')]})
            return self.send(404, {'error': 'nf'})
        if u.path == '/api/radar' and (self.bearer() or self.session()):
            d = q.get('date', [None])[0]
            runs = list_radar(d or q.get('from', [None])[0], d or q.get('to', [None])[0])
            with db() as c: days = [r[0] for r in c.execute('SELECT DISTINCT label FROM radar_runs')]
            return self.send(200, {'runs': runs, 'today': today(), 'days': sorted({run_day({'label': x}) for x in days if re.search(r'\d{4}-\d{2}-\d{2}', x)}, reverse=True)})
        if u.path == '/api/briefs' and self.bearer(): return self.send(200, {'briefs': list_briefs()})
        if u.path == '/api/tg' and (self.bearer() or self.session()):
            d = q.get('date', [None])[0]
            try: page = max(0, int(q.get('page', ['0'])[0])); per = max(0, min(60, int(q.get('per', ['5'])[0])))
            except ValueError: page, per = 0, 5
            return self.send(200, list_tg(d or q.get('from', [None])[0], d or q.get('to', [None])[0], page, per))
        if not self.session():
            if u.path.startswith('/api/'): return self.send(401, {'error': 'login'})
            return self.send(200, LOGIN.replace('{{E}}', ''), 'text/html; charset=utf-8')
        if u.path == '/': return self.send(200, PAGE, 'text/html; charset=utf-8')
        if u.path == '/api/items':
            v = q.get('view', ['urgent'])[0]
            if v not in ('urgent', 'open', 'low', 'snoozed', 'done', 'ignored', 'all'): v = 'urgent'
            un = q.get('unread', ['0'])[0] == '1'
            return self.send(200, {'items': view_rows(v, q.get('q', [''])[0][:100], un), 'counts': counts(), 'today': today()})
        if u.path == '/api/briefs': return self.send(200, {'briefs': list_briefs()})
        m = re.fullmatch(r'/api/briefs/(\d+)/pdf', u.path)
        if m:
            data, label = brief_pdf(int(m.group(1)))
            if not data: return self.send(404, {'error': 'nf'})
            from urllib.parse import quote
            return self.send(200, data, 'application/pdf', headers=[('Content-Disposition', "inline; filename*=UTF-8''" + quote(f'推特书签简报-{label}.pdf'))])
        m = re.fullmatch(r'/api/items/([\w-]+)/history', u.path)
        if m: return self.send(200, {'events': history(m.group(1))})
        if u.path == '/logout': return self.send(302, '', headers=[('Location', self.base + '/'), ('Set-Cookie', f'xbm=; Max-Age=0; Path={self.base or "/"}')])
        self.send(404, {'error': 'nf'})
    def do_POST(self):
        u = self.route()
        try: b = self.body()
        except Exception: return self.send(400, {'error': 'bad body'})
        if u.path == '/login':
            if hmac.compare_digest(str(b.get('p', '')), PASSWORD):
                tok = sign(str(int(time.time()) + 90*86400))
                return self.send(302, '', headers=[('Location', self.base + '/'), ('Set-Cookie', f'xbm={tok}; Max-Age={90*86400}; Path={self.base or "/"}; HttpOnly; Secure; SameSite=Lax')])
            time.sleep(1); return self.send(200, LOGIN.replace('{{E}}', '<div class=e>密码不对</div>'), 'text/html; charset=utf-8')
        if u.path == '/api/agent/ingest':
            if not self.bearer(): return self.send(401, {'error': 'unauthorized'})
            return self.send(200, ingest(b))
        if u.path == '/api/agent/radar':
            if not self.bearer(): return self.send(401, {'error': 'unauthorized'})
            try: return self.send(200, post_radar(b))
            except (ValueError, TypeError, AttributeError) as e: return self.send(400, {'error': 'bad value: %s' % e})
        if u.path == '/api/agent/tg':
            if not self.bearer(): return self.send(401, {'error': 'unauthorized'})
            try: return self.send(200, post_tg(b))
            except (ValueError, TypeError, AttributeError) as e: return self.send(400, {'error': 'bad value: %s' % e})
        if u.path in ('/api/briefs', '/api/agent/brief'):
            if not self.bearer(): return self.send(401, {'error': 'unauthorized'})
            try: return self.send(200, post_brief(b))
            except (ValueError, TypeError) as e: return self.send(400, {'error': 'bad value: %s' % e})
        if not self.session(): return self.send(401, {'error': 'login'})
        if self.headers.get('X-Requested-With') != 'xbm': return self.send(403, {'error': 'csrf'})
        m = re.fullmatch(r'/api/items/([\w-]+)', u.path)
        if m:
            try: r = update(m.group(1), b)
            except ValueError: return self.send(400, {'error': 'bad value'})
            return self.send(200 if r else 404, r or {'error': 'nf'})
        self.send(404, {'error': 'nf'})

    def do_DELETE(self):
        u = self.route(); q = parse_qs(u.query)
        if u.path == '/api/agent/radar' and self.bearer():
            ok = delete_radar(q.get('label', [''])[0]); return self.send(200 if ok else 404, {'deleted': ok})
        if u.path == '/api/agent/tg' and self.bearer():
            d = q.get('date', [''])[0]; w = q.get('window', [None])[0]
            if not re.fullmatch(D_RE, d) or (w and not re.fullmatch(W_RE, w)): return self.send(400, {'error': 'bad value'})
            n = delete_tg(d, w); return self.send(200, {'deleted': n})
        self.send(404, {'error': 'nf'})

if __name__ == '__main__':
    init(); ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
