#!/usr/bin/env bash
# Полная подготовка бэкенда на macOS (Homebrew PostgreSQL@16, без Docker).
export HOMEBREW_NO_AUTO_UPDATE=1
set -euo pipefail
BACKEND_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BACKEND_DIR"

export PATH="/opt/homebrew/opt/postgresql@16/bin:/usr/local/opt/postgresql@16/bin:$PATH"

echo "==> 1/5 PostgreSQL через Homebrew"
if ! command -v initdb &>/dev/null; then
  brew install postgresql@16
fi

echo "==> 2/5 Запуск службы Postgres"
brew services start postgresql@16 || brew services restart postgresql@16
sleep 3

echo "==> 3/5 База technostrelka"
createdb technostrelka 2>/dev/null || true

MAC_USER="$(whoami)"
DB_URL="postgresql+psycopg2://${MAC_USER}@127.0.0.1:5432/technostrelka"

echo "==> 4/5 Python venv и зависимости"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
fi
# Подставляем URL под локального пользователя macOS (типично для Homebrew Postgres)
if grep -q '^DATABASE_URL=' .env; then
  sed -i.bak "s|^DATABASE_URL=.*|DATABASE_URL=${DB_URL}|" .env && rm -f .env.bak
else
  echo "DATABASE_URL=${DB_URL}" >> .env
fi

LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "")
echo ""
echo "==> DATABASE_URL в .env: $DB_URL"
if [[ -n "$LAN_IP" ]]; then
  echo "==> IP вашего Mac в Wi‑Fi: $LAN_IP"
  # Картинки/аватары с телефона: ссылки должны указывать на Mac, не на 127.0.0.1
  if grep -q '^PUBLIC_BASE_URL=' .env 2>/dev/null; then
    sed -i.bak "s|^PUBLIC_BASE_URL=.*|PUBLIC_BASE_URL=http://${LAN_IP}:8000|" .env && rm -f .env.bak
  else
    echo "PUBLIC_BASE_URL=http://${LAN_IP}:8000" >> .env
  fi
  echo "==> PUBLIC_BASE_URL в .env: http://${LAN_IP}:8000"
else
  echo "==> Не удалось определить IP Wi‑Fi. Задайте PUBLIC_BASE_URL в .env вручную (URL вашего Mac:8000)."
fi
echo ""

echo "==> 5/5 Миграции и сиды"
alembic upgrade head
python scripts/seed_data.py || true

ROOT_DIR="$(cd "$BACKEND_DIR/.." && pwd)"
LP="$ROOT_DIR/local.properties"
if  [[ -n "$LAN_IP" ]] && [[ -f "$LP" ]]; then
  if grep -q '^api.base.url=' "$LP" 2>/dev/null; then
    sed -i.bak "s|^api.base.url=.*|api.base.url=http://${LAN_IP}:8000/api/v1/|" "$LP" && rm -f "$LP.bak"
  else
    echo "" >> "$LP"
    echo "# FastAPI с Mac — телефон в той же Wi‑Fi сети" >> "$LP"
    echo "api.base.url=http://${LAN_IP}:8000/api/v1/" >> "$LP"
  fi
  echo "==> В $LP добавлен api.base.url для сборки Android под физический телефон."
fi

echo ""
echo "Готово."
echo "Запуск сервера (оставьте терминал открытым):"
echo "  cd \"$BACKEND_DIR\" && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "Проверка в браузере: http://127.0.0.1:8000/docs"
