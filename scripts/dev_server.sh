#!/usr/bin/env bash
# Запуск uvicorn из папки backend (после активации venv и миграций).
set -e
cd "$(dirname "$0")/.."
if [[ ! -f .env ]]; then
  echo "Скопируйте .env.example в .env и при необходимости поправьте DATABASE_URL"
  exit 1
fi
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
