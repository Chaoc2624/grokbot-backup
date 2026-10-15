#!/usr/bin/env bash
# Crash-restart loop around forwarder.py (started detached by start.sh). Env is inherited.
cd "$(dirname "$0")"
while true; do
  python3 -u "$PWD/forwarder.py" >>"$HOME/.wechat/forwarder.out" 2>&1
  rc=$?
  [ -f "$HOME/.wechat/STOP" ] && exit 0
  echo "$(date '+%F %T') forwarder exited rc=$rc, restarting in 5s" >>"$HOME/.wechat/forwarder.out"
  sleep 5
done
