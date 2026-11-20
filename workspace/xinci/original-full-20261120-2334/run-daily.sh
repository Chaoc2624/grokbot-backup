#!/bin/bash
set -euo pipefail
OUT=/workspace/xinci/original-full-20261120-2334
cd "$OUT"
# Load key into process only
set -a
# shellcheck disable=SC1091
. /workspace/xinci/.env
set +a
export PYTHONUNBUFFERED=1
export PYTHONPATH=/workspace/xinci/repo
# Do not inherit or invent paid X tokens
unset X_BEARER_TOKEN X_API_KEY TWITTER_BEARER_TOKEN TWITTER_TOKEN || true
echo "START $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "CMD: PYTHONPATH=/workspace/xinci/repo python3 -m radar daily --skip x --new-sites --sellers --feeds --config /workspace/xinci/repo/config.json --state $OUT/state --out $OUT/report.md"
echo "CWD: $OUT"
echo "VERSION_PIN: new-term-radar 0.6.0 (existing /workspace/xinci/repo, no git pull)"
python3 -m radar daily \
  --skip x \
  --new-sites --sellers --feeds \
  --config /workspace/xinci/repo/config.json \
  --state "$OUT/state" \
  --out "$OUT/report.md"
ec=$?
echo "END_EXIT=$ec $(date '+%Y-%m-%d %H:%M:%S %Z')"
exit $ec
