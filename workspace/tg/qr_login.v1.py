import asyncio, os, time, threading, logging, html, io
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import qrcode
from telethon import TelegramClient
from telethon.network import ConnectionHttp
from telethon.tl.functions import PingRequest
import random

# The box's egress intercepts raw TCP (MTProto TCP transports get an HTTP 400 from a proxy),
# but plain HTTP to the DC IPs on port 80 passes. Force MTProto-over-HTTP on port 80 (no TLS).
from telethon.network.connection.http import HttpPacketCodec
class FixedHttpCodec(HttpPacketCodec):
    # Telethon's stock codec compares line[-1] (int) to b'\n' and always fails.
    async def read_packet(self, reader):
        length = None
        while True:
            line = await reader.readline()
            if not line or not line.endswith(b'\n'):
                raise asyncio.IncompleteReadError(line, None)
            if line.lower().startswith(b'content-length:'):
                length = int(line.split(b':', 1)[1].strip())
            elif line in (b'\r\n', b'\n') and length is not None:
                if length == 0:  # empty long-poll reply; wait for the next response
                    length = None
                    continue
                return await reader.readexactly(length)

# MTProto-over-HTTP: the server holds content-less POSTs (pure acks) for ~25 s, and since
# HTTP/1.1 responses are in order this stalls everything behind them. Attach an
# http_wait(max_wait=0) to every ack batch so the server answers those immediately.
from telethon.extensions.messagepacker import MessagePacker
from telethon.network.requeststate import RequestState
from telethon.tl.types import MsgsAck
from telethon.tl.types import HttpWait as HttpWaitRequest
_orig_append = MessagePacker.append
def _append(self, state):
    _orig_append(self, state)
    if isinstance(state.request, MsgsAck):
        _orig_append(self, RequestState(HttpWaitRequest(max_delay=0, wait_after=0, max_wait=0)))
MessagePacker.append = _append

class ConnectionHttp80(ConnectionHttp):
    packet_codec = FixedHttpCodec
    def __init__(self, ip, port, dc_id, **kw):
        super().__init__(ip, 80, dc_id, **kw)

async def poller(client, stop):
    # HTTP transport only delivers server-pushed updates (e.g. QR accepted) in responses
    # to our requests, so ping frequently while waiting.
    while not stop.is_set():
        try:
            await client(PingRequest(ping_id=random.getrandbits(63)))
        except Exception as e:
            log.info('ping error %s', type(e).__name__)
        await asyncio.sleep(2)
from telethon.errors import SessionPasswordNeededError, PasswordHashInvalidError

TG = os.path.expanduser('~/.tg')
SESSION = os.path.join(TG, 'halo')
STATUS = os.path.join(TG, 'login_status.txt')
PWFILE = os.path.join(TG, '2fa.txt')
QRPNG = os.path.join(TG, 'qr.png')
LOG = os.path.join(TG, 'login.log')
TOTAL = 15 * 60
PW_WAIT = 10 * 60

logging.basicConfig(filename=LOG, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logging.getLogger('telethon').setLevel(logging.WARNING)
log = logging.getLogger('qrlogin')

state = {'phase': 'starting', 'msg': 'Starting...', 'qr_ver': 0}
lock = threading.Lock()

def set_state(phase, msg):
    with lock:
        state['phase'] = phase; state['msg'] = msg
    log.info('state=%s %s', phase, msg if phase != 'qr' else '')

def write_status(s):
    with open(STATUS, 'w') as f: f.write(s)
    os.chmod(STATUS, 0o600)

def render_qr(url):
    img = qrcode.make(url, box_size=12, border=4)
    tmp = QRPNG + '.tmp'
    img.save(tmp, format='PNG'); os.replace(tmp, QRPNG); os.chmod(QRPNG, 0o600)
    with lock: state['qr_ver'] += 1

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.startswith('/qr.png'):
            try:
                data = open(QRPNG, 'rb').read()
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

async def wait_2fa(client):
    set_state('need_2fa', 'NEED 2FA PASSWORD'); write_status('need_2fa')
    end = time.time() + PW_WAIT
    while time.time() < end:
        if os.path.exists(PWFILE):
            try:
                pw = open(PWFILE).read().strip('\r\n')
            finally:
                try: os.remove(PWFILE)
                except FileNotFoundError: pass
            log.info('2fa file found and deleted; attempting sign-in')
            try:
                await client.sign_in(password=pw)
                return True
            except PasswordHashInvalidError:
                log.warning('2fa password invalid; waiting for a new 2fa.txt')
                set_state('need_2fa', 'NEED 2FA PASSWORD (last one was wrong)')
        await asyncio.sleep(5)
    log.error('timed out waiting for 2fa password')
    return False

async def main():
    threading.Thread(target=serve, daemon=True).start()
    write_status('pending')
    creds = {}
    for line in open(os.path.join(TG, 'creds.env')):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1); creds[k.strip()] = v.strip().strip('"').strip("'")
    client = TelegramClient(SESSION, int(creds['TG_API_ID']), creds['TG_API_HASH'],
                            connection=ConnectionHttp80, device_model='Halo Digest (box)', system_version='Linux', app_version='1.0')
    deadline = time.time() + TOTAL
    try:
        set_state('connecting', 'Connecting to Telegram...')
        try:
            await asyncio.wait_for(client.connect(), 60)
        except Exception as e:
            set_state('error', f'CONNECTION ERROR: {type(e).__name__}: {e}'); write_status('conn_error'); return
        if not client.is_connected():
            set_state('error', 'CONNECTION ERROR: not connected'); write_status('conn_error'); return
        try: os.chmod(SESSION + '.session', 0o600)
        except FileNotFoundError: pass
        log.info('connected to MTProto')
        if await client.is_user_authorized():
            me = await client.get_me()
        else:
            stop = asyncio.Event(); ptask = asyncio.create_task(poller(client, stop))
            qr = await client.qr_login()
            render_qr(qr.url); set_state('qr', 'Scan this QR with Telegram')
            me = None
            while time.time() < deadline:
                try:
                    tmo = max(5, min((qr.expires.timestamp() - time.time()), deadline - time.time()))
                    await qr.wait(timeout=tmo)
                    me = await client.get_me(); break
                except asyncio.TimeoutError:
                    if time.time() >= deadline: break
                    await qr.recreate(); render_qr(qr.url); log.info('QR recreated')
                except SessionPasswordNeededError:
                    if await wait_2fa(client): me = await client.get_me()
                    break
            stop.set(); ptask.cancel()
            if me is None:
                if state['phase'] == 'need_2fa':
                    set_state('error', 'TIMED OUT waiting for 2FA password'); write_status('timeout_2fa')
                else:
                    set_state('error', 'TIMED OUT (QR not scanned in 15 min)'); write_status('timeout')
                return
        set_state('ok', f'LOGGED IN as {me.first_name}'); write_status('ok')
        log.info('logged in, user id %s', me.id)
        try: os.remove(QRPNG)
        except FileNotFoundError: pass
    except Exception as e:
        log.exception('fatal'); set_state('error', f'ERROR: {type(e).__name__}: {e}'); write_status('error')
    finally:
        await client.disconnect()
        try: os.chmod(SESSION + '.session', 0o600)
        except FileNotFoundError: pass
        await asyncio.sleep(120)  # keep final page visible briefly

asyncio.run(main())
