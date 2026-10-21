#!/bin/bash
while true; do /workspace/tg/board_sync/sync.sh >> /workspace/tg/board_sync/sync.log 2>&1; sleep 600; done
