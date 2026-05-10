#!/bin/bash
set -euo pipefail

RUN_DATE="${1:-$(date +%F)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT_FROM_SCRIPT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$REPO_ROOT_FROM_SCRIPT}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [ ! -d "$PROJECT_ROOT/eternareturn_DB" ]; then
  PROJECT_ROOT="$REPO_ROOT_FROM_SCRIPT"
fi

cd "$PROJECT_ROOT/eternareturn_DB"

echo "[spot-training] run_date=$RUN_DATE"
echo "[spot-training] project_root=$PROJECT_ROOT"
echo "[spot-training] starting dependency install"
$PYTHON_BIN -m pip install --upgrade pip
$PYTHON_BIN -m pip install -r requirements.txt

echo "[spot-training] starting daily_rank_pipeline.py"
$PYTHON_BIN daily_rank_pipeline.py --run-date "$RUN_DATE"

echo "[spot-training] pipeline finished successfully"
