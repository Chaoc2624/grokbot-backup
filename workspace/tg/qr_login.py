"""Telegram QR login for the box (MTProto over HTTP:80 via tgnet).

Flow (done by hand rather than QRLogin.wait so every step is logged and 2FA runs
immediately on the same DC/connection that imported the token):
  exportLoginToken -> show QR -> wait for UpdateLoginToken (pings carry it over HTTP;
  also re-export every ~25 s as a fallback poll) -> exportLoginToken again ->
    LoginToken         : still waiting / expired -> new QR
    LoginTokenMigrateTo: switch to that DC (fresh auth key), importLoginToken there
    LoginTokenSuccess  : done
  importLoginToken / export -> SESSION_PASSWORD_NEEDED ->
    account.getPassword + auth.checkPassword(compute_check) right away on that same
    connection, password from env TG_2FA, else ~/.tg/2fa.txt (polled 5 s, 10 min).
"""
import asyncio, os, sys, time, threading, logging, html, random, hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import qrcode
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tgnet import make_client
from telethon import events
from telethon.errors import SessionPasswordNeededError, PasswordHashInvalidError, AuthKeyUnregisteredError
from telethon.password import compute_check
from telethon.tl import types, functions
from telethon.tl.functions import PingRequest

TG = os.path.expanduser('~/.tg')
SESSION = os.path.join(TG, 'halo')
STATUS = os.path.join(TG, 'login_status.txt')
PWFILE = os.path.join(TG, '2fa.txt')
QRPNG = os.path.join(TG, 'qr.png')
LOG = os.path.join(TG, 'login.log')
TOTAL = 15 * 60
PW_WAIT = 10 * 60

class NoPayload(logging.Filter):
    # Telethon INFO lines that dump raw response bytes could contain account data.
    def filter(self, r):
        m = r.getMessage()
        return 'without parent request' not in m and 'resent the older message' not in m
h = logging.FileHandler(LOG); h.addFilter(NoPayload())
h.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s'))
logging.basicConfig(level=logging.INFO, handlers=[h])
for n in ('telethon.crypto', 'telethon.extensions', 'telethon.network.mtprotostate'):
    logging.getLogger(n).setLevel(logging.WARNING)
log = logging.getLogger('qrlogin')

state = {'phase': 'starting', 'msg': 'Starting...', 'qr_ver': 0}
lock = threading.Lock()

def set_state(phase, msg):
    with lock:
        state['phase'] = phase; state['msg'] = msg
    log.info('state=%s %s', phase, '' if phase == 'qr' else msg)

def write_status(s):
    with open(STATUS, 'w') as f: f.write(s)
    os.chmod(STATUS, 0o600)

def render_qr(token_bytes):
    import base64
    url = 'tg://login?token=' + base64.urlsafe_b64encode(token_bytes).decode().rstrip('=')
    img = qrcode.make(url, box_size=12, border=4)
    tmp = QRPNG + '.tmp'
    img.save(tmp, format='PNG'); os.replace(tmp, QRPNG); os.chmod(QRPNG, 0o600)
    with lock: state['qr_ver'] += 1

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.startswith('/qr.png'):
            try: data = open(QRPNG, 'rb').read()
            except FileNotFoundError:
                self.send_response(404); self.end_headers(); return
            self.send_response(200); self.send_header('Content-Type', 'image/png')
            self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(data); return
        if self.path.startswith('/status'):
            with lock: body = f"{state['phase']}\n".encode()
            self.send_response(200); self.send_header('Content-Type', 'text/plain'); self.end_headers(); self.wfile.write(body); return
        with lock: phase, msg, ver = state['phase'], state['msg'], state['qr_ver']
        img = f'<img src="/qr.png?v={ver}&t={int(time.time())}" style="width:min(90vw,90vh);image-rendering:pixelated">' if phase == 'qr' else ''
        page = f'''<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="3">
<title>Telegram QR login</title></head><body style="font-family:sans-serif;text-align:center;background:#fff">
<h1 id="status">{html.escape(msg)}</h1>{img}
<p style="color:#666">Telegram → Settings → Devices → Link Desktop Device. Auto-refreshes every 3 s.</p></body></html>'''
        b = page.encode()
        self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(b)

def serve():
    ThreadingHTTPServer(('127.0.0.1', 8765), H).serve_forever()

def keyfp(client):
    k = client._sender.auth_key.key
    return hashlib.sha256(k).hexdigest()[:8] if k else None

class Pinger:
    """HTTP transport only returns server pushes inside replies, so ping while idle."""
    def __init__(self, client): self.client = client; self.paused = False; self.stop = False
    async def run(self):
        while not self.stop:
            if not self.paused and self.client.is_connected():
                try: await self.client(PingRequest(ping_id=random.getrandbits(63)))
                except Exception as e: log.info('ping error %s', type(e).__name__)
            await asyncio.sleep(2)

async def do_2fa(client):
    set_state('need_2fa', 'NEED 2FA PASSWORD'); write_status('need_2fa')
    log.info('2FA needed on DC %s key %s', client.session.dc_id, keyfp(client))
    end = time.time() + PW_WAIT
    tried_env = False
    while time.time() < end:
        if not tried_env and os.environ.get('TG_2FA'):
            pw, src = os.environ['TG_2FA'], 'env'; tried_env = True
            log.info('using 2FA password from env TG_2FA')
        else:
            pw, src = await get_password_file_only(end - time.time())
            if pw is None: break
        set_state('need_2fa', 'Checking 2FA password...')
        pwd = await client(functions.account.GetPasswordRequest())
        log.info('got password params (has_password=%s) on DC %s key %s', pwd.has_password, client.session.dc_id, keyfp(client))
        try:
            res = await client(functions.auth.CheckPasswordRequest(compute_check(pwd, pw)))
        except PasswordHashInvalidError:
            log.warning('2FA password from %s rejected', src)
            set_state('need_2fa', 'NEED 2FA PASSWORD (last one was wrong; write ~/.tg/2fa.txt)')
            continue
        return res.user
    return None

async def get_password_file_only(remaining):
    end = time.time() + max(0, remaining)
    while time.time() < end:
        if os.path.exists(PWFILE):
            try: pw = open(PWFILE).read().strip('\r\n')
            finally:
                try: os.remove(PWFILE)
                except FileNotFoundError: pass
            log.info('2FA file found and deleted'); return pw, 'file'
        await asyncio.sleep(5)
    return None, None

async def qr_flow(client, pinger, deadline):
    req = lambda: functions.auth.ExportLoginTokenRequest(client.api_id, client.api_hash, [])
    scanned = asyncio.Event()
    async def on_token(_u):
        log.info('UpdateLoginToken received'); scanned.set()
    client.add_event_handler(on_token, events.Raw(types.UpdateLoginToken))
    try:
        cur_token = None; expires = 0
        while time.time() < deadline:
            try:
                resp = await client(req())
                log.info('exportLoginToken -> %s', type(resp).__name__)
                if isinstance(resp, types.auth.LoginTokenMigrateTo):
                    pinger.paused = True
                    log.info('migrating to DC %s (old DC %s key %s)', resp.dc_id, client.session.dc_id, keyfp(client))
                    set_state('migrating', f'Scanned. Moving to DC {resp.dc_id}...')
                    await client._switch_dc(resp.dc_id)   # sets new DC, drops key, reconnects -> fresh key
                    log.info('now on DC %s key %s; importLoginToken', client.session.dc_id, keyfp(client))
                    pinger.paused = False
                    resp = await client(functions.auth.ImportLoginTokenRequest(resp.token))
                    log.info('importLoginToken -> %s', type(resp).__name__)
                if isinstance(resp, types.auth.LoginTokenSuccess):
                    return resp.authorization.user
                if isinstance(resp, types.auth.LoginToken):
                    if resp.token != cur_token:
                        cur_token = resp.token; render_qr(resp.token)
                        expires = resp.expires.timestamp()
                        set_state('qr', 'Scan this QR with Telegram')
                        log.info('new QR (expires in %ds)', int(expires - time.time()))
            except SessionPasswordNeededError:
                pinger.paused = False
                try:
                    return await do_2fa(client)
                except AuthKeyUnregisteredError:
                    # Pending-2FA authorisation was lost server-side. Start over on this DC
                    # with a fresh key so the user can simply scan the new QR again.
                    log.error('AUTH_KEY_UNREGISTERED during 2FA on DC %s key %s; resetting key and showing a new QR',
                              client.session.dc_id, keyfp(client))
                    pinger.paused = True
                    client._sender.auth_key.key = None; client.session.auth_key = None
                    client.session.save()
                    await client._disconnect(); await client.connect()
                    pinger.paused = False; cur_token = None; expires = 0
                    set_state('connecting', '2FA step failed; generating a new QR - please scan again')
                    continue
            # wait for scan event, token expiry, or 25 s fallback poll
            scanned.clear()
            wait_s = max(3, min(expires - time.time(), 25, deadline - time.time()))
            try: await asyncio.wait_for(scanned.wait(), wait_s)
            except asyncio.TimeoutError: pass
        return None
    finally:
        client.remove_event_handler(on_token)

async def main():
    threading.Thread(target=serve, daemon=True).start()
    write_status('pending')
    client = make_client(SESSION)
    deadline = time.time() + TOTAL
    pinger = Pinger(client); ptask = None
    try:
        set_state('connecting', 'Connecting to Telegram...')
        try: await asyncio.wait_for(client.connect(), 60)
        except Exception as e:
            set_state('error', f'CONNECTION ERROR: {type(e).__name__}: {e}'); write_status('conn_error'); return
        os.chmod(SESSION + '.session', 0o600)
        log.info('connected DC %s key %s', client.session.dc_id, keyfp(client))
        if await client.is_user_authorized():
            me = await client.get_me()
        else:
            ptask = asyncio.create_task(pinger.run())
            user = await qr_flow(client, pinger, deadline)
            if user is None:
                if state['phase'].startswith('need_2fa'):
                    set_state('error', 'TIMED OUT waiting for 2FA password'); write_status('timeout_2fa')
                else:
                    set_state('error', 'TIMED OUT (QR not scanned in 15 min)'); write_status('timeout')
                return
            await client._on_login(user)
            me = await client.get_me()
        set_state('ok', f'LOGGED IN as {me.first_name}'); write_status('ok')
        log.info('logged in, user id %s, DC %s', me.id, client.session.dc_id)
        try: os.remove(QRPNG)
        except FileNotFoundError: pass
    except Exception as e:
        log.exception('fatal'); set_state('error', f'ERROR: {type(e).__name__}: {e}'); write_status('error')
    finally:
        pinger.stop = True
        if ptask: ptask.cancel()
        await client.disconnect()
        try: os.chmod(SESSION + '.session', 0o600)
        except FileNotFoundError: pass
        await asyncio.sleep(120)  # keep final page visible briefly

if __name__ == '__main__':
    asyncio.run(main())
