#!/usr/bin/env bash
# Idempotent: start the WeChat forwarder detached unless it is already running.
# Run it from a Grok Bot shell so the webhook env vars are inherited.
set -u
D="$(cd "$(dirname "$0")" && pwd)"; S="$HOME/.wechat"; PF="$S/forwarder.pid"
mkdir -p "$S"; chmod 700 "$S"
if [ -f "$PF" ] && kill -0 "$(cat "$PF")" 2>/dev/null && grep -q "wechat/run.sh" "/proc/$(cat "$PF")/cmdline" 2>/dev/null; then
  echo "already running (pid $(cat "$PF"))"; exit 0
fi
if [ -z "${WECHAT_ROUTINE_WEBHOOK_URL:-}" ] || [ -z "${WECHAT_ROUTINE_WEBHOOK_KEY:-}" ]; then
  echo "WARNING: webhook env vars not set in this shell; messages will queue in ~/.wechat/pending.json until restarted from a Grok Bot shell" >&2
fi
rm -f "$S/STOP"
touch "$S/forwarder.out"; chmod 600 "$S/forwarder.out"
setsid nohup bash "$D/run.sh" </dev/null >/dev/null 2>&1 &
echo $! >"$PF"; chmod 600 "$PF"
sleep 1
if kill -0 "$(cat "$PF")" 2>/dev/null; then echo "started (pid $(cat "$PF"))"; else echo "failed to start; see $S/forwarder.out" >&2; exit 1; fi
