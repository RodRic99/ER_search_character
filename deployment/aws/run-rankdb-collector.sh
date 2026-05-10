#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT_FROM_SCRIPT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$REPO_ROOT_FROM_SCRIPT}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
LOG_DIR="${PROJECT_ROOT}/eternareturn_DB/logs"

if [ ! -d "$PROJECT_ROOT/eternareturn_DB" ]; then
  PROJECT_ROOT="$REPO_ROOT_FROM_SCRIPT"
fi

ENV_FILE="${PROJECT_ROOT}/.env.collector"
if [ ! -f "$ENV_FILE" ]; then
  echo "[collector-runner] missing env file: $ENV_FILE"
  echo "[collector-runner] copy deployment/aws/.env.collector.example to .env.collector first."
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

mkdir -p "$LOG_DIR"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG_PATH="${LOG_DIR}/rankdb_collect_${TIMESTAMP}.log"

cd "$PROJECT_ROOT/eternareturn_DB"

echo "[collector-runner] project_root=$PROJECT_ROOT" | tee -a "$LOG_PATH"
echo "[collector-runner] collector_mode=${COLLECTOR_MODE:-recent}" | tee -a "$LOG_PATH"
echo "[collector-runner] log_path=$LOG_PATH" | tee -a "$LOG_PATH"

$PYTHON_BIN -m pip install -r requirements.txt >> "$LOG_PATH" 2>&1

if [ "${COLLECTOR_MODE:-recent}" = "manual" ]; then
  if [ -z "${START_GAME_ID:-}" ]; then
    echo "[collector-runner] START_GAME_ID is required when COLLECTOR_MODE=manual" | tee -a "$LOG_PATH"
    exit 1
  fi

  ARGS=(
    "manual_collect_rankdb_from_id.py"
    "--start-game-id" "${START_GAME_ID}"
    "--max-scan-count" "${MAX_SCAN_COUNT:-50000}"
    "--max-consecutive-missing" "${MAX_CONSECUTIVE_MISSING:-300}"
    "--recent-hours-cutoff" "${RECENT_HOURS_CUTOFF:-2}"
  )

  if [ "${TRUNCATE_FIRST:-false}" != "true" ]; then
    ARGS+=("--no-truncate")
  fi

  "$PYTHON_BIN" "${ARGS[@]}" 2>&1 | tee -a "$LOG_PATH"
else
  "$PYTHON_BIN" collect_recent_rankdb.py \
    --max-scan-count "${MAX_SCAN_COUNT:-5000}" \
    --max-consecutive-missing "${MAX_CONSECUTIVE_MISSING:-50}" \
    --recent-hours-cutoff "${RECENT_HOURS_CUTOFF:-2}" 2>&1 | tee -a "$LOG_PATH"
fi
