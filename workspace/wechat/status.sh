#!/usr/bin/env bash
S="$HOME/.wechat"; PF="$S/forwarder.pid"
if [ -f "$PF" ] && kill -0 "$(cat "$PF")" 2>/dev/null; then
  echo "forwarder: running (supervisor pid $(cat "$PF"), python pid $(pgrep -f 'wechat/forwarder.py' | tr '\n' ' '))"
else
  echo "forwarder: NOT running  ->  bash /workspace/wechat/start.sh"
fi
[ -s "$S/ilink_creds.json" ] && echo "creds: present" || echo "creds: missing (scan QR to bind)"
[ -s "$S/context.json" ] && echo "context_token: present (saved $(python3 -c "import json;print(json.load(open('$S/context.json')).get('saved_at_iso'))" 2>/dev/null))" || echo "context_token: none (send ClawBot a message)"
echo "STATUS: $(cat "$S/STATUS" 2>/dev/null || echo '-')"
[ -s "$S/pending.json" ] && echo "pending webhook posts: $(python3 -c "import json;print(len(json.load(open('$S/pending.json'))))" 2>/dev/null)"
echo "--- last log lines ---"
tail -n "${1:-8}" "$S/forwarder.log" 2>/dev/null || echo "(no log yet)"
