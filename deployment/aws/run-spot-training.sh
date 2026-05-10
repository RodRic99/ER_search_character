#!/bin/bash
set -euo pipefail

RUN_DATE="${1:-$(date +%F)}"
PROJECT_ROOT="${PROJECT_ROOT:-$HOME/ER_search_character}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$PROJECT_ROOT/eternareturn_DB"

echo "[spot-training] run_date=$RUN_DATE"
echo "[spot-training] project_root=$PROJECT_ROOT"
echo "[spot-training] starting dependency install"
$PYTHON_BIN -m pip install --upgrade pip
$PYTHON_BIN -m pip install -r requirements.txt

echo "[spot-training] starting daily_rank_pipeline.py"
$PYTHON_BIN daily_rank_pipeline.py --run-date "$RUN_DATE"

echo "[spot-training] pipeline finished successfully"
