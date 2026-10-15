#!/usr/bin/env bash
S="$HOME/.wechat"; PF="$S/forwarder.pid"
touch "$S/STOP"
if [ -f "$PF" ] && kill -0 "$(cat "$PF")" 2>/dev/null; then
  kill -TERM -- "-$(cat "$PF")" 2>/dev/null || kill -TERM "$(cat "$PF")"
  for _ in 1 2 3 4 5 6 7 8 9 10; do kill -0 "$(cat "$PF")" 2>/dev/null || break; sleep 0.5; done
  kill -0 "$(cat "$PF")" 2>/dev/null && kill -KILL -- "-$(cat "$PF")" 2>/dev/null
  echo "stopped"
else
  echo "not running"
fi
pkill -f "wechat/forwarder.py" 2>/dev/null || true
rm -f "$PF"
