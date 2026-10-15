"""Telethon networking shim for this box.

The box's egress intercepts raw TCP to Telegram (MTProto TCP transports get
`HTTP/1.1 400` from a Pingora proxy), but plain HTTP POSTs to http://<DC-IP>:80/api
pass. So we run MTProto-over-HTTP on port 80, with fixes for Telethon's HTTP transport.
Usage:  from tgnet import make_client;  client = make_client(session_path)
"""
import asyncio, os, logging
from telethon import TelegramClient
from telethon.network import ConnectionHttp
from telethon.network.connection.http import HttpPacketCodec
from telethon.extensions.messagepacker import MessagePacker
from telethon.network.requeststate import RequestState
from telethon.tl.types import MsgsAck, HttpWait

log = logging.getLogger('tgnet')
TG = os.path.expanduser('~/.tg')


class FixedHttpCodec(HttpPacketCodec):
    # Stock codec compares line[-1] (an int) with b'\n' -> always raises.
    async def read_packet(self, reader):
        length = None
        status = None
        while True:
            line = await reader.readline()
            if not line or not line.endswith(b'\n'):
                raise asyncio.IncompleteReadError(line, None)
            if status is None and line.startswith(b'HTTP/'):
                status = line.strip()
                if b' 200 ' not in status + b' ':
                    log.warning('HTTP status from DC %s: %s', self._conn._ip, status.decode(errors='replace'))
            elif line.lower().startswith(b'content-length:'):
                length = int(line.split(b':', 1)[1].strip())
            elif line in (b'\r\n', b'\n') and status is not None:
                if not length:
                    # empty long-poll reply: wait for the next response
                    length = None; status = None
                    continue
                return await reader.readexactly(length)


class ConnectionHttp80(ConnectionHttp):
    """MTProto over plain HTTP, always port 80 (also after DC migration)."""
    packet_codec = FixedHttpCodec

    def __init__(self, ip, port, dc_id, **kw):
        super().__init__(ip, 80, dc_id, **kw)


# Over HTTP the server holds content-less POSTs (pure acks) for ~25 s; responses are
# in order on the keep-alive connection, so that stalls everything. Attach
# http_wait(max_wait=0) to every ack batch so those are answered immediately.
_orig_append = MessagePacker.append
def _append(self, state):
    _orig_append(self, state)
    if isinstance(state.request, MsgsAck):
        _orig_append(self, RequestState(HttpWait(max_delay=0, wait_after=0, max_wait=0)))
if not getattr(MessagePacker, '_tgnet_patched', False):
    MessagePacker.append = _append
    MessagePacker._tgnet_patched = True


def load_creds(path=os.path.join(TG, 'creds.env')):
    creds = {}
    for line in open(path):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            creds[k.strip()] = v.strip().strip('"').strip("'")
    return int(creds['TG_API_ID']), creds['TG_API_HASH']


def make_client(session, **kw):
    api_id, api_hash = load_creds()
    kw.setdefault('device_model', 'Halo Digest (box)')
    kw.setdefault('system_version', 'Linux')
    kw.setdefault('app_version', '1.0')
    return TelegramClient(session, api_id, api_hash, connection=ConnectionHttp80, **kw)
