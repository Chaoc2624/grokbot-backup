#!/usr/bin/env bash
# grokbot-backup daily sync. Exit nonzero on any failure. Log: /home/box/backup/last.log
set -euo pipefail
B=/home/box/backup; R=$B/repo; LOG=$B/last.log
REMOTE=git@github.com:Chaoc2624/grokbot-backup.git
export GIT_SSH_COMMAND="ssh -i $HOME/.ssh/grokbot_backup -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o BatchMode=yes -o ConnectTimeout=20"
exec > >(tee "$LOG") 2>&1
echo "== $(date '+%F %T %Z') sync start"
if [ ! -d "$R/.git" ]; then
  mkdir -p "$R"; git -C "$R" init -q -b main; git -C "$R" remote add origin "$REMOTE"
  git -C "$R" fetch -q origin main 2>/dev/null && git -C "$R" reset -q origin/main || true
fi
git -C "$R" config user.name "grokbot-backup"; git -C "$R" config user.email "grokbot-backup@users.noreply.github.com"
python3 $B/backup_helper.py stage "$R"
[ -f $B/RESTORE.md ] && cp $B/RESTORE.md "$R/RESTORE.md"
python3 $B/backup_helper.py scan "$R"
cd "$R"; git add -A
if git diff --cached --quiet; then echo "no changes"; else git commit -q -m "backup $(date '+%F %T')"; fi
git push origin main   # never force
echo "OK $(git rev-parse --short HEAD) files=$(git ls-files | wc -l)"
