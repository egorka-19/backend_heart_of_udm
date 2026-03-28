# Technostrelka FastAPI backend

Этот каталог — **отдельный сервис**: его можно держать в своём GitHub-репозитории независимо от Android-клиента.

### Выложить на GitHub (первый раз)

1. На [github.com/new](https://github.com/new) создайте **пустой** репозиторий (без README), например `technostrelka-api`.
2. В терминале:

```bash
cd /путь/к/technostrelka5/backend
git init
git add .
git commit -m "Initial commit: FastAPI backend"
git branch -M main
git remote add origin https://github.com/ВАШ_ЛОГИН/technostrelka-api.git
git push -u origin main
```

Если установлен [GitHub CLI](https://cli.github.com/) (`gh auth login` уже выполнен), из папки `backend` можно одной командой создать репозиторий и запушить:

```bash
gh repo create technostrelka-api --private --source=. --remote=origin --push
```

(Замените `technostrelka-api` и `--private` / `--public` по желанию.)

После `git add` в репозиторий **не попадут** `.venv/`, `.env` и папка `uploads/` — они перечислены в `.gitignore`. Секреты храните только локально; на сервере задайте переменные окружения или свой `.env`.

**Android-проект:** укажите URL нового API в `local.properties` (`api.base.url=...`) или в `build.gradle`, как в README ниже.

## Python

Рекомендуется **3.11–3.13**. На **3.14** используйте зависимости из текущего `requirements.txt` (SQLAlchemy ≥ 2.0.38 и новее, в проекте зафиксирован 2.0.48). Если после обновления Python снова увидите ошибки в `Mapped[...]` при `alembic`, выполните в venv: `pip install -U -r requirements.txt`.

## Быстрый старт (macOS / Linux)

### 1. PostgreSQL

**Вариант A — Docker (проще всего)**

Установите [Docker Desktop](https://www.docker.com/products/docker-desktop/), затем в папке `backend`:

```bash
docker compose up -d
```

Поднимется БД `technostrelka` на `localhost:5432`, логин/пароль `postgres`/`postgres` (как в `.env.example`).

**Вариант B — свой PostgreSQL**

Создайте базу `technostrelka` и пользователя или поправьте `DATABASE_URL` в `.env`.

### 2. Python и зависимости

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

В `.env` при необходимости задайте:

- `DATABASE_URL` — если БД не на `localhost:5432` с дефолтными учётками
- `SECRET_KEY` — любая длинная случайная строка
- `PUBLIC_BASE_URL` — с какого URL отдаются ссылки на файлы:
  - эмулятор Android: `http://10.0.2.2:8000`
  - браузер на том же ПК: `http://127.0.0.1:8000`

### 3. Миграции и тестовые данные

```bash
alembic upgrade head
python scripts/seed_data.py
```

Если `seed_data.py` пишет `Already seeded, skip` — это нормально.

### 4. Запуск API-сервера

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Окно терминала **нельзя закрывать**, пока тестируете приложение.

Проверка в браузере: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) — должна открыться Swagger.

- API: `http://localhost:8000/api/v1`
- OpenAPI: `http://localhost:8000/docs`
- Загрузки: `http://localhost:8000/uploads/...`

## Android

В `app/build.gradle` поле `API_BASE_URL`:

- **Эмулятор** (по умолчанию): `http://10.0.2.2:8000/api/v1/` — так уже задано в `build.gradle`
- **Реальное устройство по Wi‑Fi**: замените на `http://ВАШ_IP_КОМПЬЮТЕРА:8000/api/v1/` (например `http://192.168.1.5:8000/api/v1/`), компьютер и телефон в одной сети, фаервол разрешает порт 8000.

Если после запуска сервера всё ещё «ошибка сети» — откройте в браузере телефона `http://IP:8000/docs` и проверьте доступность.

## Setup (кратко, как раньше)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d   # или свой Postgres
alembic upgrade head
python scripts/seed_data.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
