#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 6 ]; then
  echo "Usage: $0 <rds-host> <port> <database> <user> <password> <dump-zip-path>"
  exit 1
fi

RDS_HOST="$1"
RDS_PORT="$2"
DATABASE="$3"
DB_USER="$4"
DB_PASSWORD="$5"
DUMP_ZIP_PATH="$6"

WORK_DIR="${HOME}/er_migration/import_work"
SQL_PATH="${WORK_DIR}/import.sql"

mkdir -p "${WORK_DIR}"

install_package() {
  if command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y "$@"
  elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y "$@"
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y "$@"
  else
    echo "No supported package manager found."
    exit 1
  fi
}

if ! command -v unzip >/dev/null 2>&1; then
  install_package unzip
fi

if ! command -v mysql >/dev/null 2>&1; then
  if command -v dnf >/dev/null 2>&1 || command -v yum >/dev/null 2>&1; then
    install_package mariadb105
  else
    install_package mysql-client
  fi
fi

rm -f "${SQL_PATH}"
unzip -o "${DUMP_ZIP_PATH}" -d "${WORK_DIR}"

EXTRACTED_SQL="$(find "${WORK_DIR}" -maxdepth 1 -name '*.sql' | head -n 1)"
if [ -z "${EXTRACTED_SQL}" ]; then
  echo "No SQL file found after unzip."
  exit 1
fi

mv -f "${EXTRACTED_SQL}" "${SQL_PATH}"

echo "Importing into RDS ${DATABASE} at ${RDS_HOST}:${RDS_PORT} ..."
mysql \
  --host="${RDS_HOST}" \
  --port="${RDS_PORT}" \
  --user="${DB_USER}" \
  --password="${DB_PASSWORD}" \
  --default-character-set=utf8mb4 \
  "${DATABASE}" \
  --execute="SOURCE ${SQL_PATH}"

echo "Import completed."
