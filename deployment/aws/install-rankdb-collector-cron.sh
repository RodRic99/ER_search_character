#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RUNNER_PATH="${REPO_ROOT}/deployment/aws/run-rankdb-collector.sh"
CRON_LOG="${REPO_ROOT}/eternareturn_DB/logs/rankdb_collect_cron.log"

mkdir -p "${REPO_ROOT}/eternareturn_DB/logs"
chmod +x "$RUNNER_PATH"

TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null | grep -v "run-rankdb-collector.sh" > "$TMP_CRON" || true
echo "0 */6 * * * ${RUNNER_PATH} >> ${CRON_LOG} 2>&1" >> "$TMP_CRON"
crontab "$TMP_CRON"

echo "[collector-cron] installed: every 6 hours"
echo "[collector-cron] runner: $RUNNER_PATH"
echo "[collector-cron] cron_log: $CRON_LOG"
