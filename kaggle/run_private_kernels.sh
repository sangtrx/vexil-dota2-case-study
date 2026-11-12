#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
# Pool loader injects the selected account credential only into the
# Kaggle subprocess. Do not require an interactive Kaggle OAuth login.
python="$HOME/projects/vexil-dota2-win-probability/.venv/bin/python"
"$python" "$repo/kaggle/pool_gateway.py" --action push
