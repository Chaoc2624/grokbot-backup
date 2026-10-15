#!/usr/bin/env python3
"""Get a ClawBot QR, render it, then poll until confirmed/expired. State -> ~/.wechat/bind_status.json"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ilink, segno
D = os.path.expanduser("~/.wechat"); os.makedirs(D, mode=0o700, exist_ok=True)
ST = os.path.join(D, "bind_status.json"); VC = os.path.join(D, "verify_code")
def status(**kw):
    kw["t"] = int(time.time())
    with open(ST, "w") as f: json.dump(kw, f, ensure_ascii=False)
    os.chmod(ST, 0o600)
r = ilink.get_qr()
qr, url = r["qrcode"], r["qrcode_img_content"]
png = "/workspace/wechat/clawbot_qr.png"
segno.make(url, error="m").save(png, scale=10, border=4)
status(status="qr_ready", url=url, png=png)
print(url, flush=True)
base = ilink.DEFAULT_BASE_URL; start = time.time(); sent_vc = None
while time.time() - start < 600:
    vc = None
    if os.path.exists(VC):
        vc = open(VC).read().strip() or None
    s = ilink.poll_qr(qr, base_url=base, verify_code=vc if vc and vc != sent_vc else None)
    if vc and vc != sent_vc: sent_vc = vc
    st = s.get("status", "wait")
    if st == "scaned_but_redirect" and s.get("redirect_host"):
        base = "https://" + s["redirect_host"]; status(status=st, url=url); continue
    if st == "confirmed":
        c = ilink.creds_from_confirmed(s); c["baseurl"] = c["base_url"]
        try:
            ns = ilink._post(c["base_url"], "ilink/bot/msg/notifystart", {"base_info": ilink.base_info()}, token=c["bot_token"], timeout=10)
            print("notifystart", ns.get("ret"), ns.get("errcode"), flush=True)
        except Exception as e:
            print("notifystart exc", str(e)[:120], flush=True)
        ilink.save_creds(c)
        if os.path.exists(VC): os.remove(VC)
        status(status="confirmed", user_id_set=bool(c.get("ilink_user_id"))); print("confirmed"); break
    if st in ("expired", "verify_code_blocked", "binded_redirect"):
        status(status=st, url=url); print(st); break
    status(status=st, url=url)
    time.sleep(1)
else:
    status(status="timeout", url=url)
