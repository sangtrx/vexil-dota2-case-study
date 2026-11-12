#!/usr/bin/env bash
set -euo pipefail

# Run ONLY after Kaggle login. No tokens printed, copied or committed.
# All kernels private, CPU, internet disabled. Do not publish the dataset.
repo="$(cd "$(dirname "$0")/.." && pwd)"
stage=/home/ai-agent/.cache/vexil-bible-kaggle-stage-20261113
kaggle=/home/ai-agent/.local/bin/kaggle

if ! command -v "$kaggle" >/dev/null 2>&1; then
  echo "Kaggle CLI missing; STOP" >&2
  exit 3
fi

if ! "$kaggle" kernels list --mine --page-size 1 >/dev/null 2>&1; then
  echo "Kaggle not authenticated. Run: kaggle auth login" >&2
  exit 4
fi

python="$(dirname "$repo")/vexil-dota2-win-probability/.venv/bin/python"
"$python" "$repo/kaggle/prepare_private_runs.py"

# Kaggle datasets create is PRIVATE by default; do not pass --public.
echo "Creating private input dataset (one-time; fail if same ID exists)."
"$kaggle" datasets create -p "$stage/dataset"
for mode in scores instability maxt chronology; do
  echo "Submitting PRIVATE CPU kernel: $mode"
  "$kaggle" kernels push -p "$repo/kaggle/kernel_$mode"
done
echo "Submitted 4 hosted kernels, not yet verified COMPLETE."
echo "Check status and download receipts with kaggle/verify_hosted_kernels.sh."
