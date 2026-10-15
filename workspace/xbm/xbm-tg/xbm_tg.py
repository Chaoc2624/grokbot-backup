#!/opt/xbm-tg/venv/bin/python
"""xbm-tg — read-only Telegram puller for Halo 的看板 (x.omnitools.cc #tg).

Runs as user xbmtg, listens on 127.0.0.1:10093 (internal HTTP, X-Internal-Token required);
the board (/opt/xbm-board/app.py) is the only client and does user auth.
Read-only by design: only auth (QR login / 2FA), getDialogs/getHistory/resolve. It never sends,
never marks read (no ReadHistory/ReadAcknowledge), never joins/leaves.

Endpoints (JSON):
  GET  /status[?watch=1]      login state (+ QR as data-URI while logging in), current job
  POST /login/qr              start (or keep alive) the QR login loop
  POST /login/password        {password} for 2FA — never logged, never written to disk
  POST /pull                  {groups:[key..], since:unix, until:unix, label?} -> {id}
  GET  /pull/current          latest job ; GET /pull/<id> ; POST /pull/<id>/cancel
Data: /opt/xbm-tg/data/raw.db  (tg_raw: one row per message, PK (chat_id,msg_id); tg_state; tg_jobs)
"""
import asyncio, base64, datetime as dt, io, json, logging, os, secrets, sqlite3, sys, time, hmac
from telethon import TelegramClient, events, errors, functions, types, utils
import qrcode, qrcode.image.svg

HOME = '/opt/xbm-tg'; DATA = HOME + '/data'
SESSION = DATA + '/xbm-tg'                       # -> xbm-tg.session
DBP = DATA + '/raw.db'
GROUPS = HOME + '/groups.json'
TOKEN = open(DATA + '/internal.token').read().strip()
API_ID = int(os.environ['TG_API_ID']); API_HASH = os.environ['TG_API_HASH']
PORT = int(os.environ.get('XBM_TG_PORT', '10093'))
TZ = dt.timezone(dt.timedelta(hours=8))
CAP_PER_GROUP = int(os.environ.get('XBM_TG_CAP', '20000'))
QR_IDLE = 90          # stop the QR loop when nobody has polled /status?watch=1 for this long

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(levelname)s %(name)s %(message)s')
logging.getLogger('telethon').setLevel(logging.WARNING)
log = logging.getLogger('xbm-tg')

def bj(ts): return dt.datetime.fromtimestamp(ts, TZ)
def nows(): return dt.datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')

# ---------------- db ----------------
def db():
    c = sqlite3.connect(DBP, timeout=15); c.row_factory = sqlite3.Row
    c.execute('PRAGMA journal_mode=DELETE'); return c

def init_db():
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS tg_raw(chat_id INTEGER NOT NULL, msg_id INTEGER NOT NULL, gkey TEXT, ts INTEGER, date TEXT, hm TEXT,
          sender_id INTEGER, sender TEXT, text TEXT, media TEXT, reply_to INTEGER, fwd TEXT, job_id TEXT, fetched_at TEXT,
          PRIMARY KEY(chat_id, msg_id));
        CREATE INDEX IF NOT EXISTS tg_raw_date ON tg_raw(date, chat_id, ts);
        CREATE INDEX IF NOT EXISTS tg_raw_job ON tg_raw(job_id);
        CREATE TABLE IF NOT EXISTS tg_state(chat_id INTEGER PRIMARY KEY, gkey TEXT, max_msg_id INTEGER, max_ts INTEGER, last_pull TEXT);
        CREATE TABLE IF NOT EXISTS tg_jobs(id TEXT PRIMARY KEY, created_at TEXT, finished_at TEXT, params TEXT, status TEXT,
          fetched INTEGER, added INTEGER, errors TEXT);
        ''')
    os.chmod(DBP, 0o600)

def load_groups():
    return {g['key']: g for g in json.load(open(GROUPS, encoding='utf-8'))}

# ---------------- telegram client ----------------
S = {'state': 'starting', 'me': None, 'error': None, 'hint': None, 'qr_url': None, 'qr_exp': 0, 'qr_ver': 0,
     'last_watch': 0, 'flood_until': 0}
client = None
qr_task = None

def mk_client(updates):
    return TelegramClient(SESSION, API_ID, API_HASH, device_model='Halo 看板 (xbm-tg)', system_version='Linux server',
                          app_version='xbm-tg 1.0', lang_code='zh', system_lang_code='zh-CN',
                          flood_sleep_threshold=0, receive_updates=updates, catch_up=False,
                          connection_retries=3, retry_delay=2, auto_reconnect=True, request_retries=3)

async def reconnect(updates):
    global client
    if client is not None:
        try: await client.disconnect()
        except Exception: pass
    client = mk_client(updates)
    await client.connect()
    try: os.chmod(SESSION + '.session', 0o600)
    except FileNotFoundError: pass

def who(u):
    return {'id': u.id, 'name': ' '.join(x for x in (u.first_name, u.last_name) if x) or (u.username or str(u.id)),
            'username': u.username}

async def became_authorized(user=None):
    S.update(state='authorized', error=None, hint=None, qr_url=None)
    await reconnect(False)           # no update stream once logged in: we only pull history on demand
    me = user or await client.get_me()
    S['me'] = who(me)
    log.info('authorized')
    asyncio.create_task(warm())

async def warm():
    """Fill the session's entity cache (access hashes) so group ids resolve. Read-only."""
    try:
        n = 0
        async for _ in client.iter_dialogs(): n += 1
        log.info('dialogs cached: %d', n)
    except errors.FloodWaitError as e:
        log.warning('warm flood %ss', e.seconds)
    except Exception as e:
        log.warning('warm failed: %s', type(e).__name__)

async def startup():
    while True:
        try:
            await reconnect(False)
            if await client.is_user_authorized():
                S['state'] = 'authorized'; S['me'] = who(await client.get_me()); log.info('session authorized')
                asyncio.create_task(warm())
            else:
                S['state'] = 'logged_out'; log.info('not logged in')
            return
        except Exception as e:
            S.update(state='error', error='连接 Telegram 失败：%s' % type(e).__name__)
            log.warning('connect failed: %r', e); await asyncio.sleep(30)

def qr_svg(url):
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2)
    b = io.BytesIO(); img.save(b)
    return 'data:image/svg+xml;base64,' + base64.b64encode(b.getvalue()).decode()

async def qr_loop():
    """Export login tokens; on UpdateLoginToken (or periodic re-export) finish the login."""
    evt = asyncio.Event()
    async def on_tok(_u): evt.set()
    try:
        await reconnect(True)
        if await client.is_user_authorized():
            await became_authorized(); return
        client.add_event_handler(on_tok, events.Raw(types.UpdateLoginToken))
        S.update(state='qr', error=None)
        req = functions.auth.ExportLoginTokenRequest(API_ID, API_HASH, [])
        while True:
            if time.time() - S['last_watch'] > QR_IDLE:
                log.info('qr idle, stopping'); S.update(state='logged_out', qr_url=None); return
            evt.clear()
            try:
                resp = await client(req)
            except errors.FloodWaitError as e:
                S.update(state='qr_wait', error='Telegram 要求等待 %d 秒后再生成二维码' % e.seconds, qr_url=None)
                await asyncio.sleep(e.seconds + 1); S['state'] = 'qr'; continue
            if isinstance(resp, types.auth.LoginTokenMigrateTo):
                log.info('login token migrate to dc %s', resp.dc_id)
                await client._switch_dc(resp.dc_id)
                resp = await client(functions.auth.ImportLoginTokenRequest(resp.token))
            if isinstance(resp, types.auth.LoginTokenSuccess):
                user = resp.authorization.user
                await client._on_login(user)
                client.remove_event_handler(on_tok)
                await became_authorized(user); return
            if isinstance(resp, types.auth.LoginToken):
                url = 'tg://login?token=' + base64.urlsafe_b64encode(resp.token).decode().rstrip('=')
                if url != S['qr_url']:
                    S.update(qr_url=url, qr_svg=qr_svg(url), qr_exp=resp.expires.timestamp(), qr_ver=S['qr_ver'] + 1)
                left = max(2.0, min(25.0, resp.expires.timestamp() - time.time() - 4))
                try: await asyncio.wait_for(evt.wait(), timeout=left)
                except asyncio.TimeoutError: pass
                continue
            raise TypeError(type(resp).__name__)
    except errors.SessionPasswordNeededError:
        S.update(state='password', qr_url=None, error=None)
        try:
            pw = await client(functions.account.GetPasswordRequest()); S['hint'] = pw.hint
        except Exception: S['hint'] = None
        log.info('2fa password needed')
    except asyncio.CancelledError:
        raise
    except Exception as e:
        log.warning('qr loop error: %r', e)
        S.update(state='error', error='二维码登录出错：%s' % type(e).__name__, qr_url=None)
    finally:
        try: client.remove_event_handler(on_tok)
        except Exception: pass

def start_qr():
    global qr_task
    S['last_watch'] = time.time()
    if S['state'] in ('authorized', 'password', 'starting'): return
    if qr_task and not qr_task.done(): return
    S.update(state='qr', qr_url=None, error=None)
    qr_task = asyncio.create_task(qr_loop())

async def submit_password(pw):
    if S['state'] != 'password': return 409, {'error': 'not_waiting_password', 'state': S['state']}
    try:
        user = await client.sign_in(password=pw)
    except errors.PasswordHashInvalidError:
        S['error'] = '两步验证密码不对，请重试'; return 400, {'error': 'bad_password'}
    except errors.FloodWaitError as e:
        S['error'] = '尝试太频繁，Telegram 要求等待 %d 秒' % e.seconds; return 429, {'error': 'flood', 'seconds': e.seconds}
    except Exception as e:
        S['error'] = '登录失败：%s' % type(e).__name__; return 500, {'error': type(e).__name__}
    finally:
        pw = None
    await became_authorized(user if isinstance(user, types.User) else None)
    return 200, {'ok': True, 'state': S['state']}

# ---------------- pull jobs ----------------
JOBS = {}; CUR = {'id': None}; TASKS = {}

def job_view(j):
    if not j: return None
    o = {k: v for k, v in j.items() if not k.startswith('_')}
    tot = max(1, j['groups_total'])
    o['percent'] = 100.0 if j['status'] == 'done' else round(min(99.9, (j['groups_done'] + j['_frac']) / tot * 100), 1)
    o['wait_left'] = max(0, int(j['_wait_until'] - time.time())) if j['_wait_until'] else 0
    return o

def sender_name(m):
    s = m.sender
    if isinstance(s, types.User):
        return ' '.join(x for x in (s.first_name, s.last_name) if x) or s.username or str(s.id)
    if s is not None: return getattr(s, 'title', None) or str(getattr(s, 'id', ''))
    return m.post_author or ''

def media_desc(m):
    md = m.media
    if md is None: return None
    if isinstance(md, types.MessageMediaPhoto): return '图片'
    if isinstance(md, types.MessageMediaWebPage): return None
    if isinstance(md, types.MessageMediaDocument):
        d = md.document
        if m.sticker: return '贴纸'
        if m.gif: return 'GIF'
        if m.video: return '视频'
        if m.voice: return '语音'
        if m.audio: return '音频'
        fn = next((a.file_name for a in getattr(d, 'attributes', []) if isinstance(a, types.DocumentAttributeFilename)), None)
        return '文件' + (f'：{fn}' if fn else '')
    if isinstance(md, types.MessageMediaPoll): return '投票'
    if isinstance(md, (types.MessageMediaGeo, types.MessageMediaVenue, types.MessageMediaGeoLive)): return '位置'
    if isinstance(md, types.MessageMediaContact): return '名片'
    return '媒体'

def fwd_desc(m):
    f = m.fwd_from
    if not f: return None
    return f.from_name or ('频道/用户 %s' % utils.get_peer_id(f.from_id) if f.from_id else '转发')

async def resolve(g):
    try: return await client.get_input_entity(g['id'])
    except (ValueError, TypeError): pass
    await warm()
    try: return await client.get_input_entity(g['id'])
    except (ValueError, TypeError):
        if g.get('username'): return await client.get_input_entity(g['username'])
        raise

def flush(rows):
    if not rows: return 0
    with db() as c:
        before = c.total_changes
        c.executemany('INSERT OR IGNORE INTO tg_raw(chat_id,msg_id,gkey,ts,date,hm,sender_id,sender,text,media,reply_to,fwd,job_id,fetched_at) '
                      'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)', rows)
        n = c.total_changes - before
    rows.clear(); return n

def save_state(g, max_id, max_ts):
    with db() as c:
        r = c.execute('SELECT max_msg_id, max_ts FROM tg_state WHERE chat_id=?', (g['id'],)).fetchone()
        mi = max(max_id or 0, (r[0] or 0) if r else 0); mt = max(max_ts or 0, (r[1] or 0) if r else 0)
        c.execute('INSERT OR REPLACE INTO tg_state(chat_id,gkey,max_msg_id,max_ts,last_pull) VALUES(?,?,?,?,?)', (g['id'], g['key'], mi, mt, nows()))

def save_job(j):
    with db() as c:
        c.execute('INSERT OR REPLACE INTO tg_jobs(id,created_at,finished_at,params,status,fetched,added,errors) VALUES(?,?,?,?,?,?,?,?)',
                  (j['id'], j['created_at'], j.get('finished_at'), json.dumps({'since': j['since'], 'until': j['until'], 'groups': j['group_keys'], 'label': j.get('label')}, ensure_ascii=False),
                   j['status'], j['fetched'], j['added'], json.dumps(j['errors'], ensure_ascii=False)))

async def run_job(j, groups):
    since, until = j['since'], j['until']
    span = max(1, until - since)
    until_dt = dt.datetime.fromtimestamp(until, dt.timezone.utc)
    try:
        for gi, g in enumerate(groups):
            if j['_cancel']: break
            j.update(current_group=g['title'], current_index=gi + 1, current_fetched=0); j['_frac'] = 0.0
            try:
                ent = await resolve(g)
            except Exception as e:
                j['errors'].append(f"{g['title']}：无法打开这个群（{type(e).__name__}）"); j['groups_done'] += 1; continue
            offset_id = 0; got = 0; added = 0; rows = []; max_id = 0; max_ts = 0; done = False
            while not done and not j['_cancel']:
                try:
                    kw = dict(offset_id=offset_id) if offset_id else dict(offset_date=until_dt)
                    async for m in client.iter_messages(ent, wait_time=0.6, **kw):
                        if j['_cancel']: done = True; break
                        ts = int(m.date.timestamp())
                        if ts < since: done = True; break
                        offset_id = m.id
                        if ts > until: continue
                        j['_frac'] = min(1.0, (until - ts) / span)
                        if isinstance(m, types.MessageService) or getattr(m, 'action', None): continue
                        d = bj(ts)
                        rows.append((g['id'], m.id, g['key'], ts, d.strftime('%Y-%m-%d'), d.strftime('%H:%M:%S'), m.sender_id, sender_name(m)[:120],
                                     (m.message or '')[:8000], media_desc(m), m.reply_to_msg_id if m.reply_to else None, fwd_desc(m), j['id'], nows()))
                        got += 1; j['fetched'] += 1; j['current_fetched'] = got
                        if m.id > max_id: max_id = m.id; max_ts = ts
                        if len(rows) >= 200:
                            n = flush(rows); added += n; j['added'] += n
                        if got >= CAP_PER_GROUP:
                            j['truncated'].append(g['title']); done = True; break
                    else:
                        done = True
                except errors.FloodWaitError as e:
                    n = flush(rows); added += n; j['added'] += n
                    j['_wait_until'] = time.time() + e.seconds + 1
                    j['note'] = f'Telegram 限流，等待 {e.seconds} 秒后继续'
                    log.info('flood wait %ss in job %s', e.seconds, j['id'])
                    await asyncio.sleep(e.seconds + 1)
                    j['_wait_until'] = 0; j['note'] = None
                except (errors.AuthKeyUnregisteredError, errors.UnauthorizedError, errors.AuthKeyDuplicatedError) as e:
                    S.update(state='logged_out', me=None, error='Telegram 会话已失效，请重新扫码登录')
                    raise
                except (ConnectionError, OSError, asyncio.TimeoutError) as e:
                    j['errors'].append(f"{g['title']}：网络中断（{type(e).__name__}），已保存已拉到的部分"); done = True
                except errors.RPCError as e:
                    j['errors'].append(f"{g['title']}：{e.__class__.__name__}"); done = True
            n = flush(rows); added += n; j['added'] += n
            if max_id: save_state(g, max_id, max_ts)
            j['per_group'].append({'key': g['key'], 'title': g['title'], 'fetched': got, 'added': added})
            j['groups_done'] += 1; j['_frac'] = 0.0
        j['status'] = 'cancelled' if j['_cancel'] else 'done'
    except asyncio.CancelledError:
        j['status'] = 'cancelled'
    except (errors.AuthKeyUnregisteredError, errors.UnauthorizedError, errors.AuthKeyDuplicatedError) as e:
        j['status'] = 'error'; j['errors'].append('Telegram 会话已失效（%s），请重新扫码登录' % type(e).__name__)
    except Exception as e:
        log.exception('job failed'); j['status'] = 'error'; j['errors'].append('拉取出错：%s' % type(e).__name__)
    finally:
        j['current_group'] = None; j['finished_at'] = nows(); j['_wait_until'] = 0
        save_job(j); log.info('job %s %s fetched=%d added=%d', j['id'], j['status'], j['fetched'], j['added'])

def start_job(b):
    cur = JOBS.get(CUR['id'])
    if cur and cur['status'] == 'running': return 409, {'error': 'busy', 'job': job_view(cur)}
    if S['state'] != 'authorized': return 409, {'error': 'not_logged_in', 'state': S['state']}
    try: since = int(b['since']); until = int(b['until'])
    except (KeyError, TypeError, ValueError): return 400, {'error': 'since/until'}
    if not (0 < since < until) or until - since > 31 * 86400 + 60: return 400, {'error': 'range'}
    G = load_groups(); keys = [k for k in (b.get('groups') or []) if k in G]
    if not keys: return 400, {'error': 'groups'}
    groups = [G[k] for k in keys]
    jid = dt.datetime.now(TZ).strftime('%Y%m%d%H%M%S') + secrets.token_hex(2)
    j = {'id': jid, 'status': 'running', 'created_at': nows(), 'finished_at': None, 'label': b.get('label'),
         'since': since, 'until': until, 'since_bj': bj(since).strftime('%Y-%m-%d %H:%M'), 'until_bj': bj(until).strftime('%Y-%m-%d %H:%M'),
         'group_keys': keys, 'groups_total': len(groups), 'groups_done': 0, 'current_group': None, 'current_index': 0, 'current_fetched': 0,
         'fetched': 0, 'added': 0, 'errors': [], 'truncated': [], 'per_group': [], 'note': None,
         '_frac': 0.0, '_wait_until': 0, '_cancel': False}
    JOBS[jid] = j; CUR['id'] = jid
    for k in sorted(JOBS)[:-20]: JOBS.pop(k, None)
    save_job(j)
    TASKS[jid] = asyncio.create_task(run_job(j, groups))
    return 200, {'id': jid, 'job': job_view(j)}

def last_job():
    j = JOBS.get(CUR['id'])
    if j: return job_view(j)
    with db() as c:
        r = c.execute('SELECT * FROM tg_jobs ORDER BY created_at DESC LIMIT 1').fetchone()
    if not r: return None
    p = json.loads(r['params'] or '{}')
    st = r['status'] if r['status'] != 'running' else 'interrupted'
    return {'id': r['id'], 'status': st, 'created_at': r['created_at'], 'finished_at': r['finished_at'], 'fetched': r['fetched'], 'added': r['added'],
            'errors': json.loads(r['errors'] or '[]'), 'group_keys': p.get('groups'), 'since': p.get('since'), 'until': p.get('until'), 'percent': 100.0 if st == 'done' else 0}

def status(watch):
    if watch: S['last_watch'] = time.time()
    o = {'state': S['state'], 'me': S['me'] if S['state'] == 'authorized' else None, 'error': S['error'], 'hint': S['hint'] if S['state'] == 'password' else None,
         'job': last_job()}
    if S['state'] == 'qr' and S.get('qr_url'):
        o['qr'] = {'img': S['qr_svg'], 'ver': S['qr_ver'], 'expires_in': max(0, int(S['qr_exp'] - time.time()))}
    return o

# ---------------- tiny internal HTTP server ----------------
async def handle(reader, writer):
    code, out = 500, {'error': 'internal'}
    try:
        head = await asyncio.wait_for(reader.readuntil(b'\r\n\r\n'), 10)
        lines = head.decode('latin-1').split('\r\n')
        method, path, _ = lines[0].split(' ', 2)
        hdr = {k.strip().lower(): v.strip() for k, v in (l.split(':', 1) for l in lines[1:] if ':' in l)}
        n = int(hdr.get('content-length') or 0)
        raw = await asyncio.wait_for(reader.readexactly(n), 10) if 0 < n <= 100_000 else b''
        if not hmac.compare_digest(hdr.get('x-internal-token', ''), TOKEN):
            code, out = 401, {'error': 'unauthorized'}
        else:
            b = json.loads(raw or b'{}') if raw else {}
            p, _, q = path.partition('?')
            if method == 'GET' and p == '/status': code, out = 200, status('watch=1' in q)
            elif method == 'POST' and p == '/login/qr': start_qr(); code, out = 200, status(True)
            elif method == 'POST' and p == '/login/password':
                pw = str(b.pop('password', '') or ''); b = None
                code, out = (400, {'error': 'empty'}) if not pw else await submit_password(pw); pw = None
            elif method == 'POST' and p == '/pull': code, out = start_job(b)
            elif method == 'GET' and p == '/pull/current': code, out = 200, {'job': last_job()}
            elif method == 'GET' and p.startswith('/pull/'):
                j = JOBS.get(p[6:]); code, out = (200, {'job': job_view(j)}) if j else (404, {'error': 'nf'})
            elif method == 'POST' and p.startswith('/pull/') and p.endswith('/cancel'):
                j = JOBS.get(p[6:-7])
                if j and j['status'] == 'running': j['_cancel'] = True; code, out = 200, {'ok': True}
                else: code, out = 404, {'error': 'nf'}
            else: code, out = 404, {'error': 'nf'}
    except Exception as e:
        log.warning('http error: %s', type(e).__name__); code, out = 500, {'error': type(e).__name__}
    try:
        body = json.dumps(out, ensure_ascii=False).encode()
        writer.write(f'HTTP/1.1 {code} X\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n'.encode() + body)
        await writer.drain()
    finally:
        writer.close()

async def main():
    os.umask(0o077)
    init_db()
    srv = await asyncio.start_server(handle, '127.0.0.1', PORT)
    log.info('listening on 127.0.0.1:%d', PORT)
    asyncio.create_task(startup())
    async with srv: await srv.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
