#!/usr/bin/env bash
# Stub notify hook: called with path to FAILED file. Wire real notification here.
echo "$(date '+%F %T %Z') notify_fail called: ${1:-}" >> /home/box/backup/notify.log
