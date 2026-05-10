#!/bin/bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/ER_search_character}"
COMPOSE_FILE="${COMPOSE_FILE:-$PROJECT_ROOT/compose.aws.yaml}"
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env.aws}"
MODEL_DIR="${MODEL_DIR:-$PROJECT_ROOT/eternareturn_DB/models}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$PROJECT_ROOT"

export TRAINING_MODEL_DIR="$MODEL_DIR"

echo "[refresh-predict-api] syncing latest model artifacts from S3"
$PYTHON_BIN "$PROJECT_ROOT/deployment/aws/sync-latest-training-artifacts.py"

echo "[refresh-predict-api] restarting predict-api container"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" restart predict-api

echo "[refresh-predict-api] done"
