#!/bin/bash
# Sync TG images + metadata index to halo-board server. No summary text is sent.
set -u
H=root@192.255.151.85; DEST=/opt/xbm-board/tg-media; KEEP_DAYS=${KEEP_DAYS:-30}
cd /workspace/tg/board_sync || exit 1
exec 9>/tmp/tg-board-sync.lock; flock -n 9 || exit 0
echo "[$(date '+%F %T')] sync start"
python3 build_index.py
ssh -o BatchMode=yes -o ConnectTimeout=15 $H "mkdir -p $DEST/media $DEST/index"
[ -d /workspace/tg/media ] && rsync -a --timeout=120 -e 'ssh -o BatchMode=yes' /workspace/tg/media/ $H:$DEST/media/
rsync -a --timeout=60 -e 'ssh -o BatchMode=yes' out/index/ $H:$DEST/index/
# retention on server (and local index)
ssh -o BatchMode=yes $H "find $DEST/media -mindepth 1 -maxdepth 1 -type d -mtime +$KEEP_DAYS -exec rm -rf {} +; find $DEST/index -name '*.json' -mtime +$KEEP_DAYS -delete"
echo "[$(date '+%F %T')] sync done"
