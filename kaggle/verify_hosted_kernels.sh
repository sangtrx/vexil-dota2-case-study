#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
kaggle=/home/ai-agent/.local/bin/kaggle
stage=/home/ai-agent/.cache/vexil-bible-kaggle-stage-20261113
mkdir -p "$stage/hosted_downloads"
for mode in scores instability maxt; do
  case "$mode" in
    scores) slug=vexil-bible-proper-scores-20261113 ;;
    instability) slug=vexil-bible-selection-instability-20261113 ;;
    maxt) slug=vexil-bible-familywise-audit-20261113 ;;
  esac
  name="sangtruong/$slug"
  echo "Checking hosted kernel $name"
  "$kaggle" kernels status "$name"
  # Do not interpret an in-progress kernel as a completed execution.
  "$kaggle" kernels output "$name" -p "$stage/hosted_downloads/$mode"
done
python="$(dirname "$repo")/vexil-dota2-win-probability/.venv/bin/python"
"$python" "$repo/kaggle/verify_hosted_receipts.py" --source "$stage/hosted_downloads" --local "$stage/local_verified"
