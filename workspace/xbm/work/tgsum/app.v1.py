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
        c.executescript('''
        CREATE TABLE IF NOT EXISTS tg_pull_jobs(job_id TEXT PRIMARY KEY, since INTEGER, until INTEGER, groups TEXT, new_count INTEGER, job_status TEXT,
          sum_status TEXT DEFAULT 'none', sum_error TEXT, pending_at TEXT, notified_at TEXT, summary_at TEXT, attempts INTEGER DEFAULT 0,
          overview TEXT, created_at TEXT, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS tg_pull_summaries(id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL, rank INTEGER DEFAULT 0, grp TEXT, chat_id INTEGER,
          frm TEXT, to_ TEXT, date TEXT, msg_count INTEGER, content TEXT, created_at TEXT);
        CREATE INDEX IF NOT EXISTS tg_pull_summaries_job ON tg_pull_summaries(job_id);
        CREATE INDEX IF NOT EXISTS tg_pull_summaries_date ON tg_pull_summaries(date);
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

# ---------- 📡 TG 主动拉取（xbm-tg 服务，127.0.0.1:10093，只读会话） ----------
TG_HOME = os.environ.get('XBM_TG_HOME', '/opt/xbm-tg')
TG_SVC = os.environ.get('XBM_TG_SVC', 'http://127.0.0.1:10093')
TG_RAWDB = TG_HOME + '/data/raw.db'

def tgsvc(method, path, body=None, timeout=15):
    import urllib.request, urllib.error
    try: tok = open(TG_HOME + '/data/internal.token').read().strip()
    except OSError: return 503, {'error': 'svc_down', 'state': 'down'}
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    req = urllib.request.Request(TG_SVC + path, data=data, method=method, headers={'X-Internal-Token': tok, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        try: return e.code, json.load(e)
        except Exception: return e.code, {'error': 'svc_%d' % e.code}
    except Exception:
        return 503, {'error': 'svc_down', 'state': 'down'}

def tg_groups_cfg():
    try: return json.load(open(TG_HOME + '/groups.json', encoding='utf-8'))
    except (OSError, ValueError): return []

def rawdb():
    if not os.path.exists(TG_RAWDB): return None
    c = sqlite3.connect(f'file:{TG_RAWDB}?mode=ro', uri=True, timeout=10); c.row_factory = sqlite3.Row; return c

def tg_groups():
    st, cnt = {}, {}
    c = rawdb()
    if c:
        try:
            st = {r['chat_id']: dict(r) for r in c.execute('SELECT chat_id,max_msg_id,max_ts,last_pull FROM tg_state')}
            cnt = {r[0]: r[1] for r in c.execute('SELECT chat_id,COUNT(*) FROM tg_raw GROUP BY chat_id')}
        finally: c.close()
    out = []
    for g in tg_groups_cfg():
        s_ = st.get(g['id'], {})
        out.append({'key': g['key'], 'title': g['title'], 'tag': g.get('tag'), 'category': g.get('category'), 'default': bool(g.get('pull_default')),
                    'last_pull': s_.get('last_pull'), 'max_msg_id': s_.get('max_msg_id'),
                    'latest_at': dt.datetime.fromtimestamp(s_['max_ts'], TZ).strftime('%Y-%m-%d %H:%M') if s_.get('max_ts') else None,
                    'stored': cnt.get(g['id'], 0)})
    return out

def tg_link(g, mid):
    if not g: return None
    if g.get('username'): return f"https://t.me/{g['username']}/{mid}"
    return f"https://t.me/c/{-int(g['id']) - 1000000000000}/{mid}"

def raw_summary(frm, to):
    G = {g['id']: g for g in tg_groups_cfg()}
    c = rawdb(); days = {}
    if not c: return {'days': [], 'total': 0, 'job': None, 'pulls': pulls_in(frm, to)}
    try:
        lj = (c.execute('SELECT id FROM tg_jobs ORDER BY created_at DESC LIMIT 1').fetchone() or [None])[0]
        rows = c.execute('SELECT date, chat_id, substr(hm,1,2) h, COUNT(*) n, MIN(hm) a, MAX(hm) b, SUM(job_id IS ?) nw '
                         'FROM tg_raw WHERE date BETWEEN ? AND ? GROUP BY date, chat_id, h', (lj, frm, to)).fetchall()
    finally: c.close()
    for r in rows:
        d = days.setdefault(r['date'], {'date': r['date'], 'count': 0, 'new': 0, 'groups': {}})
        g = G.get(r['chat_id'], {})
        e = d['groups'].setdefault(r['chat_id'], {'chat': r['chat_id'], 'key': g.get('key'), 'title': g.get('title') or str(r['chat_id']), 'tag': g.get('tag'),
                                                  'order': g.get('order', 99), 'count': 0, 'new': 0, 'first': r['a'], 'last': r['b'], 'hours': []})
        e['hours'].append({'h': r['h'], 'count': r['n'], 'new': r['nw'], 'first': r['a'], 'last': r['b']})
        e['count'] += r['n']; e['new'] += r['nw']; e['first'] = min(e['first'], r['a']); e['last'] = max(e['last'], r['b'])
        d['count'] += r['n']; d['new'] += r['nw']
    out = []
    for k in sorted(days, reverse=True):
        d = days[k]; gs = sorted(d['groups'].values(), key=lambda g: (-g['count'], g['order']))
        for g in gs: g['hours'].sort(key=lambda h: h['h'], reverse=True)
        d['groups'] = gs; out.append(d)
    return {'days': out, 'total': sum(d['count'] for d in out), 'job': lj, 'pulls': pulls_in(frm, to)}

def raw_msgs(date, chat, hour=None, offset=0, limit=300):
    G = {g['id']: g for g in tg_groups_cfg()}; g = G.get(chat)
    c = rawdb()
    if not c: return {'messages': [], 'total': 0}
    try:
        lj = (c.execute('SELECT id FROM tg_jobs ORDER BY created_at DESC LIMIT 1').fetchone() or [None])[0]
        w, a = 'date=? AND chat_id=?', [date, chat]
        if hour is not None: w += ' AND substr(hm,1,2)=?'; a.append('%02d' % hour)
        total = c.execute(f'SELECT COUNT(*) FROM tg_raw WHERE {w}', a).fetchone()[0]
        rows = [dict(r) for r in c.execute(f'SELECT msg_id,hm,sender_id,sender,text,media,reply_to,fwd,job_id FROM tg_raw WHERE {w} ORDER BY ts, msg_id LIMIT ? OFFSET ?', a + [limit, offset])]
    finally: c.close()
    for r in rows:
        r['link'] = tg_link(g, r['msg_id']); r['new'] = bool(lj and r.pop('job_id') == lj)
    return {'messages': rows, 'total': total, 'offset': offset, 'limit': limit, 'group': g and g['title']}

def pull_params(b):
    # {hours:N} | {days:N} | {from:'YYYY-MM-DD HH:MM', to:'…'} (北京时间) + groups:[key…] -> service body
    nowt = int(time.time())
    if b.get('hours') not in (None, ''):
        n = float(b['hours']); assert 0 < n <= 744; since, until = nowt - int(n * 3600), nowt
    elif b.get('days') not in (None, ''):
        n = float(b['days']); assert 0 < n <= 31; since, until = nowt - int(n * 86400), nowt
    else:
        def p(v):
            v = str(v or '').strip().replace('T', ' ')
            for f in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
                try: return int(dt.datetime.strptime(v, f).replace(tzinfo=TZ).timestamp())
                except ValueError: pass
            raise ValueError('time')
        since, until = p(b.get('from')), min(p(b.get('to')) if b.get('to') else nowt, nowt)
        assert since < until and until - since <= 31 * 86400 + 60
    gs = b.get('groups') or []
    assert isinstance(gs, list) and gs
    return {'since': since, 'until': until, 'groups': [str(x)[:40] for x in gs][:60], 'label': str(b.get('label') or '')[:80]}

# ---------- 📝 拉取总结：拉取结束 -> webhook 唤醒助手 -> 助手读原始消息、总结、推回（服务器上不做总结） ----------
import threading, urllib.request, urllib.error
WEBHOOK_ENV = os.environ.get('XBM_WEBHOOK_ENV', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webhook.env'))
SUM_TIMEOUT = 15 * 60
HM_RE = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?'

def wh_cfg():
    """webhook.env: TG_SUMMARY_WEBHOOK_URL=, TG_SUMMARY_WEBHOOK_KEY=, optional TG_SUMMARY_WEBHOOK_HEADER= (default 'Authorization: Bearer {key}')."""
    kv = {}
    try:
        for l in open(WEBHOOK_ENV, encoding='utf-8'):
            l = l.strip()
            if not l or l.startswith('#') or '=' not in l: continue
            k, v = l.split('=', 1); v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in '"\'': v = v[1:-1].strip()
            kv[k.strip()] = v
    except OSError: pass
    return kv

def wh_header(cfg, key):
    if not key: return None, None
    tpl = (cfg.get('TG_SUMMARY_WEBHOOK_HEADER') or 'Authorization: Bearer {key}').strip()
    if ':' not in tpl: return tpl, key                       # "X-Webhook-Key" -> X-Webhook-Key: <key>
    name, val = tpl.split(':', 1); name = name.strip(); val = val.strip()
    if name.lower() == 'authorization' and val.lower().startswith('bearer') and key.lower().startswith('bearer '): key = key[7:].strip()
    val = val.replace('{key}', key) if '{key}' in val else (val + ' ' + key).strip()
    return name, val.replace('\r', '').replace('\n', '')

def bjs(ts): return dt.datetime.fromtimestamp(int(ts), TZ).strftime('%Y-%m-%d %H:%M') if ts else None

def rawjob(jid):
    c = rawdb()
    if not c: return None
    try: r = c.execute('SELECT * FROM tg_jobs WHERE id=?', (jid,)).fetchone()
    finally: c.close()
    return dict(r) if r else None

def job_groups(keys):
    G = {g['key']: g for g in tg_groups_cfg()}
    return [{'key': k, 'title': G.get(k, {}).get('title') or k, 'chat_id': G.get(k, {}).get('id')} for k in (keys or [])]

def register_job(j, notify=True):
    """j = tg_jobs row (terminal). Creates the board-side summary record once; new_count 0 -> 'none'."""
    if not j or j.get('status') == 'running': return False
    p = json.loads(j.get('params') or '{}'); added = int(j.get('added') or 0); ts = now()
    st = 'pending' if added > 0 else 'none'
    with db() as c:
        n = c.execute('INSERT OR IGNORE INTO tg_pull_jobs(job_id,since,until,groups,new_count,job_status,sum_status,pending_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)',
                      (j['id'], p.get('since'), p.get('until'), json.dumps(p.get('groups') or []), added, j.get('status'), st, ts if st == 'pending' else None, j.get('created_at'), ts)).rowcount
    if n and st == 'pending' and notify: threading.Thread(target=notify_job, args=(j['id'],), daemon=True).start()
    return bool(n)

def pull_row(jid):
    with db() as c: r = c.execute('SELECT * FROM tg_pull_jobs WHERE job_id=?', (jid,)).fetchone()
    return dict(r) if r else None

def ensure_row(jid, notify=True):
    r = pull_row(jid)
    if r: return r
    register_job(rawjob(jid), notify); return pull_row(jid)

def set_sum(jid, st, err=None, only_if=None):
    ts = now(); w = ' AND sum_status=?' if only_if else ''
    with db() as c:
        return c.execute(f'UPDATE tg_pull_jobs SET sum_status=?, sum_error=?, updated_at=?, summary_at=CASE WHEN ?=\'done\' THEN ? ELSE summary_at END WHERE job_id=?{w}',
                         (st, err, ts, st, ts, jid) + ((only_if,) if only_if else ())).rowcount

def notify_job(jid):
    """POST the wake-up webhook. Never logs the key or the URL."""
    r = pull_row(jid)
    if not r or r['sum_status'] != 'pending': return
    cfg = wh_cfg(); url = (cfg.get('TG_SUMMARY_WEBHOOK_URL') or '').strip(); key = (cfg.get('TG_SUMMARY_WEBHOOK_KEY') or '').strip()
    if not url or not re.match(r'https?://', url): return set_sum(jid, 'failed', '未配置通知地址', 'pending')
    body = json.dumps({'job_id': jid, 'from': bjs(r['since']), 'to': bjs(r['until']), 'groups': job_groups(json.loads(r['groups'] or '[]')),
                       'new_count': r['new_count'], 'board': PUBLIC, 'summary_api': f"{PUBLIC}/api/tg/pull/{jid}/summary"}, ensure_ascii=False).encode()
    hdr = {'Content-Type': 'application/json', 'User-Agent': 'xbm-board'}
    hn, hv = wh_header(cfg, key)
    if hn: hdr[hn] = hv
    err = None
    for i in range(4):                                       # 1 try + 3 retries
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=hdr, method='POST'), timeout=15) as resp:
                if 200 <= resp.status < 300:
                    with db() as c: c.execute("UPDATE tg_pull_jobs SET notified_at=?, attempts=attempts+1, updated_at=? WHERE job_id=? AND sum_status='pending'", (now(), now(), jid))
                    print('tg-summary webhook sent for job', jid, flush=True); return
                err = 'HTTP %d' % resp.status
        except urllib.error.HTTPError as e: err = 'HTTP %d' % e.code
        except Exception as e: err = type(e).__name__
        if i < 3: time.sleep((2, 5, 10)[i])
    with db() as c: c.execute('UPDATE tg_pull_jobs SET attempts=attempts+4 WHERE job_id=?', (jid,))
    print('tg-summary webhook failed for job', jid, err, flush=True)
    set_sum(jid, 'failed', f'通知发送失败（{err}，已重试 3 次）', 'pending')

def pull_scan():
    c = rawdb()
    if not c: return
    try: jobs = [dict(r) for r in c.execute("SELECT * FROM tg_jobs WHERE status!='running' ORDER BY created_at DESC LIMIT 50")]
    finally: c.close()
    with db() as b: have = {r[0] for r in b.execute('SELECT job_id FROM tg_pull_jobs')}
    for j in jobs:
        if j['id'] not in have: register_job(j)

def pull_watch():
    while True:
        try: pull_scan()
        except Exception as e: print('pull_watch error', type(e).__name__, flush=True)
        time.sleep(4)

def sum_view(r):
    if not r: return None
    o = {'status': r['sum_status'], 'error': r['sum_error'], 'pending_at': r['pending_at'], 'notified_at': r['notified_at'],
         'summary_at': r['summary_at'], 'new_count': r['new_count'], 'timeout': False, 'waited_min': None}
    if r['sum_status'] == 'pending' and r['pending_at']:
        try:
            w = (dt.datetime.now(TZ) - dt.datetime.strptime(r['pending_at'], '%Y-%m-%d %H:%M').replace(tzinfo=TZ)).total_seconds()
            o['waited_min'] = int(w // 60); o['timeout'] = w > SUM_TIMEOUT
        except ValueError: pass
    return o

def job_from_raw(jid):
    r = rawjob(jid)
    if not r: return None
    p = json.loads(r['params'] or '{}'); st = r['status'] if r['status'] != 'running' else 'interrupted'
    return {'id': r['id'], 'status': st, 'created_at': r['created_at'], 'finished_at': r['finished_at'], 'fetched': r['fetched'], 'added': r['added'],
            'errors': json.loads(r['errors'] or '[]'), 'group_keys': p.get('groups'), 'since': p.get('since'), 'until': p.get('until'),
            'since_bj': bjs(p.get('since')), 'until_bj': bjs(p.get('until')), 'percent': 100.0 if st == 'done' else 0}

def with_sum(job):
    if isinstance(job, dict) and job.get('id') and job.get('status') not in ('running', None):
        job['summary'] = sum_view(ensure_row(job['id']))
    return job

def get_summary(jid):
    r = ensure_row(jid, notify=False)
    if not r: return None
    with db() as c:
        items = [dict(x) for x in c.execute('SELECT grp,chat_id,frm AS "from",to_ AS "to",date,msg_count,content,rank FROM tg_pull_summaries WHERE job_id=? ORDER BY rank, id', (jid,))]
    return {'job_id': jid, 'from': bjs(r['since']), 'to': bjs(r['until']), 'groups': job_groups(json.loads(r['groups'] or '[]')),
            'summary': sum_view(r), 'overview': r['overview'], 'items': items}

def post_summary(jid, b):
    r = ensure_row(jid, notify=False)
    if not r: raise LookupError(jid)
    items = b.get('items') or []; ov = b.get('overview')
    if not isinstance(items, list) or (not items and not (ov and str(ov).strip())): raise ValueError('items')
    G = tg_groups_cfg(); byid = {g['id']: g for g in G}; byname = {}
    for g in G: byname[g['key']] = g; byname[g['title']] = g
    dflt = (bjs(r['until']) or now())[:10]; rows = []
    for k, it in enumerate(items):
        if not isinstance(it, dict): raise ValueError('item %d' % k)
        content = str(it.get('content') or '')
        if not content.strip(): raise ValueError('item %d content' % k)
        grp = str(it.get('grp') or it.get('group') or '')[:120]; cid = it.get('chat_id')
        try: cid = int(cid) if cid not in (None, '') else None
        except (TypeError, ValueError): raise ValueError('item %d chat_id' % k)
        g = byid.get(cid) if cid is not None else byname.get(grp)
        if g: cid = g['id']; grp = grp or g['title']
        if not grp and cid is None: raise ValueError('item %d grp/chat_id' % k)
        frm = str(it.get('from') or '').strip()[:19] or None; to = str(it.get('to') or '').strip()[:19] or None
        for v in (frm, to):
            if v and not re.fullmatch(HM_RE, v): raise ValueError('item %d from/to' % k)
        d = str(it.get('date') or (to or frm or dflt)[:10])
        if not re.fullmatch(D_RE, d): raise ValueError('item %d date' % k)
        mc = it.get('msg_count')
        try: mc = int(mc) if mc not in (None, '') else None
        except (TypeError, ValueError): mc = None
        rows.append((jid, k, grp or (g and g['title']) or str(cid), cid, frm, to, d, mc, content[:200000]))
    ts = now()
    with db() as c:
        c.execute('DELETE FROM tg_pull_summaries WHERE job_id=?', (jid,))
        c.executemany('INSERT INTO tg_pull_summaries(job_id,rank,grp,chat_id,frm,to_,date,msg_count,content,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)', [x + (ts,) for x in rows])
        c.execute("UPDATE tg_pull_jobs SET overview=?, sum_status='done', sum_error=NULL, summary_at=?, updated_at=? WHERE job_id=?", (str(ov)[:50000] if ov else None, ts, ts, jid))
    return {'job_id': jid, 'items': len(rows), 'overview': bool(ov), 'status': 'done'}

def delete_summary(jid, st='pending'):
    if st not in ('pending', 'none', 'failed'): raise ValueError('status')
    with db() as c:
        n = c.execute('DELETE FROM tg_pull_summaries WHERE job_id=?', (jid,)).rowcount
        c.execute('UPDATE tg_pull_jobs SET overview=NULL, sum_status=?, sum_error=NULL, summary_at=NULL, notified_at=NULL, pending_at=?, updated_at=? WHERE job_id=?',
                  (st, now() if st == 'pending' else None, now(), jid))
    return {'job_id': jid, 'deleted_items': n, 'status': st}

def retry_summary(jid):
    r = ensure_row(jid, notify=False)
    if not r: raise LookupError(jid)
    if not r['new_count']: raise ValueError('no_new')
    with db() as c: c.execute("UPDATE tg_pull_jobs SET sum_status='pending', sum_error=NULL, pending_at=?, notified_at=NULL, updated_at=? WHERE job_id=?", (now(), now(), jid))
    threading.Thread(target=notify_job, args=(jid,), daemon=True).start()
    return {'job_id': jid, 'status': 'pending'}

def job_raw(jid, offset=0, limit=1000):
    """All raw messages inside the job's time range for the job's groups (not only the ones this job added)."""
    r = rawjob(jid)
    if not r: return None
    p = json.loads(r['params'] or '{}'); gs = job_groups(p.get('groups')); ids = [g['chat_id'] for g in gs if g['chat_id'] is not None]
    T = {g['chat_id']: g['title'] for g in gs}; G = {g['id']: g for g in tg_groups_cfg()}
    c = rawdb()
    try:
        if not ids: return {'job_id': jid, 'messages': [], 'total': 0}
        w = f'chat_id IN ({",".join("?" * len(ids))}) AND ts BETWEEN ? AND ?'; a = ids + [p.get('since'), p.get('until')]
        total = c.execute(f'SELECT COUNT(*) FROM tg_raw WHERE {w}', a).fetchone()[0]
        rows = [dict(x) for x in c.execute(f'SELECT chat_id,msg_id,date,hm,sender_id,sender,text,media,reply_to,fwd,job_id FROM tg_raw WHERE {w} ORDER BY chat_id, ts, msg_id LIMIT ? OFFSET ?', a + [limit, offset])]
    finally: c.close()
    for x in rows:
        x['grp'] = T.get(x['chat_id']); x['new'] = x.pop('job_id') == jid; x['link'] = tg_link(G.get(x['chat_id']), x['msg_id'])
    return {'job_id': jid, 'from': bjs(p.get('since')), 'to': bjs(p.get('until')), 'groups': gs, 'total': total, 'offset': offset, 'limit': limit, 'messages': rows}

def pulls_in(frm, to):
    """Summary records of pull jobs whose range touches [frm, to] (dates, 北京时间), with their summary items."""
    with db() as c:
        rs = [dict(r) for r in c.execute('SELECT * FROM tg_pull_jobs ORDER BY created_at DESC, job_id DESC LIMIT 200')]
        out = []
        for r in rs:
            a, b = (bjs(r['since']) or '')[:10], (bjs(r['until']) or '')[:10]
            if not a or b < frm or a > to: continue
            items = [dict(x) for x in c.execute('SELECT grp,chat_id,frm AS "from",to_ AS "to",date,msg_count,content FROM tg_pull_summaries WHERE job_id=? ORDER BY rank, id', (r['job_id'],))]
            out.append({'job_id': r['job_id'], 'from': bjs(r['since']), 'to': bjs(r['until']), 'from_date': a, 'to_date': b, 'created_at': r['created_at'],
                        'groups': job_groups(json.loads(r['groups'] or '[]')), 'new_count': r['new_count'], 'summary': sum_view(r),
                        'overview': r['overview'], 'items': items})
            if len(out) >= 40: break
    return out

PAGE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html'), encoding='utf-8').read()
_TGL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tg-login.html')
TG_LOGIN_PAGE = open(_TGL, encoding='utf-8').read() if os.path.exists(_TGL) else '<p>tg-login.html missing</p>'
LOGIN = '''<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Halo 的看板 · 登录</title>
<style>body{font-family:-apple-system,"PingFang SC",sans-serif;background:#f4f5f7;display:flex;height:100vh;align-items:center;justify-content:center;margin:0}
form{background:#fff;padding:28px;border-radius:12px;box-shadow:0 2px 12px #0001;width:280px}input,button{width:100%;box-sizing:border-box;padding:10px;margin-top:10px;font-size:15px;border-radius:8px;border:1px solid #ccc}
button{background:#1d6fe0;color:#fff;border:0}.e{color:#c00;font-size:13px}</style></head><body><form method=post action=login><b>Halo 的看板</b>{{E}}
<input type=hidden name=next value="{{N}}"><input type=password name=p placeholder=密码 autofocus><button>登录</button></form></body></html>'''
NEXTS = ('tg-login',)
def login_page(err='', nxt=''): return LOGIN.replace('{{E}}', err).replace('{{N}}', nxt if nxt in NEXTS else '')

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
        if u.path.startswith('/api/tg/') and (self.bearer() or self.session()):
            if u.path == '/api/tg/groups': return self.send(200, {'groups': tg_groups()})
            if u.path == '/api/tg/raw':
                d = q.get('date', [None])[0]; frm = d or q.get('from', [None])[0] or today(); to = d or q.get('to', [None])[0] or today()
                if not (re.fullmatch(D_RE, frm) and re.fullmatch(D_RE, to)): return self.send(400, {'error': 'bad value'})
                return self.send(200, raw_summary(frm, to))
            if u.path == '/api/tg/raw/msgs':
                try:
                    d = q['date'][0]; ch = int(q['chat'][0]); hr = q.get('hour', [None])[0]; hr = int(hr) if hr not in (None, '') else None
                    off = max(0, int(q.get('offset', ['0'])[0])); lim = max(1, min(500, int(q.get('limit', ['300'])[0])))
                    assert re.fullmatch(D_RE, d)
                except (KeyError, ValueError, AssertionError): return self.send(400, {'error': 'bad value'})
                return self.send(200, raw_msgs(d, ch, hr, off, lim))
            if u.path == '/api/tg/login':
                code, r = tgsvc('GET', '/status' + ('?watch=1' if q.get('watch', ['0'])[0] == '1' else ''))
                if code == 503: code, r = 200, {'state': 'down', 'error': '拉取服务没有运行'}
                if isinstance(r, dict) and r.get('job'): with_sum(r['job'])
                return self.send(code, r)
            if u.path == '/api/tg/pull/current':
                code, r = tgsvc('GET', '/pull/current')
                if isinstance(r, dict) and r.get('job'): with_sum(r['job'])
                return self.send(code, r)
            m = re.fullmatch(r'/api/tg/pull/(\w+)/summary', u.path)
            if m:
                s_ = get_summary(m.group(1)); return self.send(200 if s_ else 404, s_ or {'error': 'nf'})
            m = re.fullmatch(r'/api/tg/pull/(\w+)/raw', u.path)
            if m:
                try: off = max(0, int(q.get('offset', ['0'])[0])); lim = max(1, min(5000, int(q.get('limit', ['1000'])[0])))
                except ValueError: return self.send(400, {'error': 'bad value'})
                s_ = job_raw(m.group(1), off, lim); return self.send(200 if s_ else 404, s_ or {'error': 'nf'})
            m = re.fullmatch(r'/api/tg/pull/(\w+)', u.path)
            if m:
                code, r = tgsvc('GET', '/pull/' + m.group(1))
                if code == 404 or code == 503:
                    j = job_from_raw(m.group(1))
                    if j: code, r = 200, {'job': j}
                if isinstance(r, dict) and r.get('job'): with_sum(r['job'])
                return self.send(code, r)
        if u.path == '/tg-login' and self.session(): return self.send(200, TG_LOGIN_PAGE, 'text/html; charset=utf-8')
        if not self.session():
            if u.path.startswith('/api/'): return self.send(401, {'error': 'login'})
            return self.send(200, login_page('', 'tg-login' if u.path == '/tg-login' else ''), 'text/html; charset=utf-8')
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
                nx = str(b.get('next') or ''); nx = nx if nx in NEXTS else ''
                return self.send(302, '', headers=[('Location', self.base + '/' + nx), ('Set-Cookie', f'xbm={tok}; Max-Age={90*86400}; Path={self.base or "/"}; HttpOnly; Secure; SameSite=Lax')])
            time.sleep(1); return self.send(200, login_page('<div class=e>密码不对</div>', str(b.get('next') or '')), 'text/html; charset=utf-8')
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
        if u.path.startswith('/api/tg/'):
            if not (self.bearer() or (self.session() and self.headers.get('X-Requested-With') == 'xbm')):
                return self.send(403 if self.session() else 401, {'error': 'csrf' if self.session() else 'login'})
            if u.path == '/api/tg/login/qr': return self.send(*tgsvc('POST', '/login/qr', {}))
            if u.path == '/api/tg/login/password':
                pw = str(b.pop('password', '') or ''); b = None
                code, r = tgsvc('POST', '/login/password', {'password': pw}, timeout=40); pw = None
                return self.send(code, r)
            if u.path == '/api/tg/pull':
                try: pb = pull_params(b)
                except (ValueError, TypeError, AssertionError, AttributeError): return self.send(400, {'error': 'bad value'})
                return self.send(*tgsvc('POST', '/pull', pb))
            m = re.fullmatch(r'/api/tg/pull/(\w+)/cancel', u.path)
            if m: return self.send(*tgsvc('POST', '/pull/' + m.group(1) + '/cancel', {}))
            m = re.fullmatch(r'/api/tg/pull/(\w+)/summary(?:/(fail|retry))?', u.path)
            if m:
                jid, act = m.group(1), m.group(2)
                if act != 'retry' and not self.bearer(): return self.send(401, {'error': 'unauthorized'})
                try:
                    if act == 'retry': return self.send(200, retry_summary(jid))
                    if act == 'fail':
                        if not ensure_row(jid, notify=False): return self.send(404, {'error': 'nf'})
                        set_sum(jid, 'failed', str(b.get('error') or '总结失败')[:500]); return self.send(200, {'job_id': jid, 'status': 'failed'})
                    return self.send(200, post_summary(jid, b))
                except LookupError: return self.send(404, {'error': 'nf'})
                except ValueError as e: return self.send(400, {'error': 'bad value: %s' % e})
            return self.send(404, {'error': 'nf'})
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
        m = re.fullmatch(r'/api/tg/pull/(\w+)/summary', u.path)
        if m and self.bearer():
            if not pull_row(m.group(1)): return self.send(404, {'error': 'nf'})
            try: return self.send(200, delete_summary(m.group(1), q.get('status', ['pending'])[0]))
            except ValueError: return self.send(400, {'error': 'bad value'})
        if u.path == '/api/agent/tg' and self.bearer():
            d = q.get('date', [''])[0]; w = q.get('window', [None])[0]
            if not re.fullmatch(D_RE, d) or (w and not re.fullmatch(W_RE, w)): return self.send(400, {'error': 'bad value'})
            n = delete_tg(d, w); return self.send(200, {'deleted': n})
        self.send(404, {'error': 'nf'})

if __name__ == '__main__':
    init(); threading.Thread(target=pull_watch, daemon=True).start()
    ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
