#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
kaggle=/home/ai-agent/.local/bin/kaggle
stage=/home/ai-agent/.cache/vexil-bible-kaggle-stage-20261113
mkdir -p "$stage/hosted_downloads"
for mode in scores instability maxt chronology; do
  case "$mode" in
    scores) slug=vexil-bible-proper-scores-20261113 ;;
    instability) slug=vexil-bible-selection-instability-20261113 ;;
    maxt) slug=vexil-bible-familywise-audit-20261113 ;;\n    chronology) slug=vexil-bible-chronology-audit-20261113 ;;
  esac
  name="sangtruong/$slug"
  echo "Checking hosted kernel $name"
  status="$("$kaggle" kernels status "$name")"
  printf '%s\n' "$status"
  if ! printf '%s\n' "$status" | grep -Eq 'KernelWorkerStatus[.]COMPLETE|[Ss]tatus:[[:space:]]*[Cc][Oo][Mm][Pp][Ll][Ee][Tt][Ee]'; then
    echo "Kernel not confirmed COMPLETE: $name" >&2
    exit 6
  fi
  # Do not interpret an in-progress kernel as a completed execution.
  "$kaggle" kernels output "$name" -p "$stage/hosted_downloads/$mode"
done
python="$(dirname "$repo")/vexil-dota2-win-probability/.venv/bin/python"
"$python" "$repo/kaggle/verify_hosted_receipts.py" --source "$stage/hosted_downloads" --local "$stage/local_verified"
