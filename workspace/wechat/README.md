# WeChat bridge (iLink / ClawBot)  — outbound only, no listening port

forwarder.py  getupdates long-poll -> POST {source,from_user_id,message_id,text,time[,images,image_error]} to the routine webhook
              (Authorization: Bearer $WECHAT_ROUTINE_WEBHOOK_KEY). Only the bound ilink_user_id is forwarded.
reply.py      python3 /workspace/wechat/reply.py "text"   (or stdin). Markdown stripped, 4000-char split.
              exit 0 ok | 14 token expired (-14, re-scan) | 2 ret -2 (user must message ClawBot) | 3 no creds | 4 no context
media.py      image download: CDN GET + AES-128-ECB decrypt (port of plugin cdn/pic-decrypt.ts, media/media-download.ts).
              Bound sender only. Saved to ~/.wechat/media/<message_id>_<n>.<ext> (dir 700, files 600).

Webhook body contract (for the routine):
  images       optional list of absolute file paths ON THE BOX (e.g. /home/box/.wechat/media/123_1.jpg) when the
               WeChat message contained image(s); open each with the Read tool to see it. Present only for image
               messages. text is the caption if one was sent, else "[图片]".
  image_error  optional string, set when one or more images failed to download/decrypt (message still forwarded).

start.sh / stop.sh / status.sh   (start.sh is idempotent; run.sh restarts the daemon if it crashes)
test_bridge.py  offline tests (mocked HTTP): python3 test_bridge.py

State: ~/.wechat/{media/,ilink_creds.json,cursor,context.json,seen.json,pending.json,STATUS,forwarder.log,forwarder.pid}

Env: the webhook URL/key exist only in processes spawned by Grok Bot's shell (injected per command,
not via /etc/environment, .bashrc or a login shell). The daemon inherits them from the shell that ran start.sh.
No systemd/cron on the box and no boot hook -> after a box reboot ask Grok Bot to run:
    bash /workspace/wechat/start.sh
