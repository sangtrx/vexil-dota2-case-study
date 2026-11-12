#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
python="$HOME/projects/vexil-dota2-win-probability/.venv/bin/python"
"$python" "$repo/kaggle/pool_gateway.py" --action verify
