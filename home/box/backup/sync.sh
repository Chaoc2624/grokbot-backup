#!/usr/bin/env bash
# grokbot-backup daily sync. Exit nonzero on any failure. Log: /home/box/backup/last.log
set -euo pipefail
B=/home/box/backup; R=$B/repo; LOG=$B/last.log
REMOTE=https://github.com/Chaoc2624/grokbot-backup.git
TOKFILE=$HOME/.config/grokbot-backup/token
export PATH=/usr/local/bin:/usr/bin:/bin:$PATH
exec > >(tee "$LOG") 2>&1
fail(){ rc=$?; { echo "FAILED $(date '+%F %T %Z') rc=$rc"; tail -n 30 "$LOG"; } > $B/FAILED; $B/notify_fail.sh $B/FAILED || true; exit $rc; }
trap fail ERR
echo "== $(date '+%F %T %Z') sync start"
if [ -z "${GITHUB_BACKUP_TOKEN:-}" ] && [ -r "$TOKFILE" ]; then set -a; . "$TOKFILE"; set +a; fi
[ -n "${GITHUB_BACKUP_TOKEN:-}" ] || { echo "no token"; false; }
export GIT_ASKPASS=$B/askpass.sh GIT_TERMINAL_PROMPT=0
if [ ! -d "$R/.git" ]; then mkdir -p "$R"; git -C "$R" init -q -b main; fi
git -C "$R" remote set-url origin "$REMOTE" 2>/dev/null || git -C "$R" remote add origin "$REMOTE"
git -C "$R" config user.name "grokbot-backup"; git -C "$R" config user.email "grokbot-backup@users.noreply.github.com"
git -C "$R" config --unset credential.helper || true
if git -C "$R" fetch -q origin main 2>/dev/null; then
  git -C "$R" rev-parse -q --verify HEAD >/dev/null || git -C "$R" reset -q origin/main
fi
python3 $B/backup_helper.py stage "$R"
cp $B/RESTORE.md "$R/RESTORE.md"
python3 $B/backup_helper.py scan "$R"
cd "$R"; git add -A
if git diff --cached --quiet; then echo "no changes"; else git commit -q -m "backup $(date '+%F %T')"; fi
git push origin main   # never force
echo "OK $(git rev-parse --short HEAD) files=$(git ls-files | wc -l)"
rm -f $B/FAILED
