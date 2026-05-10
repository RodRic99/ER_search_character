#!/bin/bash
set -euo pipefail

LOG_DIR="/var/log/er-training"
PROJECT_ROOT="/opt/ER_search_character"
REPO_URL="${REPO_URL:-}"
RUN_DATE="${RUN_DATE:-$(date +%F)}"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_DIR/user-data.log") 2>&1

echo "[user-data] start $(date -Is)"

dnf update -y
dnf install -y git python3 python3-pip unzip

if [ -z "$REPO_URL" ]; then
  echo "[user-data] REPO_URL is not set"
  exit 1
fi

rm -rf "$PROJECT_ROOT"
git clone "$REPO_URL" "$PROJECT_ROOT"

chmod +x "$PROJECT_ROOT/deployment/aws/run-spot-training.sh"
"$PROJECT_ROOT/deployment/aws/run-spot-training.sh" "$RUN_DATE"

echo "[user-data] training completed, shutting down"
shutdown -h now
