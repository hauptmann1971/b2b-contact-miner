# B2B Contact Miner

Python-система для поиска B2B-контактов по ключевым словам: SERP → обход сайтов → извлечение email/Telegram → сохранение в MySQL → веб-кабинет.

Подходит как портфолио-кейс по **парсингу, очередям задач и деплою** (не «скрипт на коленке»).

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Web-Flask-black.svg)
![MySQL](https://img.shields.io/badge/DB-MySQL-orange.svg)
![CI](https://img.shields.io/badge/CI-pytest%20%7C%20SonarCloud-brightgreen.svg)

## Что умеет

1. Принимает **ключевые слова** (язык + страна) через веб-UI или CLI  
2. Ищет сайты через **SERP** (Yandex / DuckDuckGo / SerpAPI)  
3. Обходит страницы (**HTTP**, при необходимости **Playwright**)  
4. Достаёт контакты: regex, JSON-LD, mailto; опционально **LLM** (YandexGPT / OpenAI / DeepSeek)  
5. Кладёт результат в **MySQL**, показывает в кабинете, отдаёт в CSV  

Очередь задач — таблица `task_queue` в MySQL (воркеры в `workers/`).

## Демо и код

| | |
|---|---|
| **Код** | этот репозиторий |
| **Веб на VPS** | демо-доступ по запросу (логин + Basic Auth) |
| **Связанный кейс** | [Crypto-currency-converter](https://github.com/hauptmann1971/Crypto-currency-converter) — живой Telegram-бот |

> Использование только по ТЗ заказчика и в рамках закона. Проект — инструмент сбора контактов для B2B-продаж, не «спам-база».

## Стек

| Слой | Технологии |
|------|------------|
| Web UI | Flask, Jinja2, static CSS/JS |
| Pipeline | `main.py` + `DatabaseTaskQueue` |
| Поиск | Yandex Search API / DuckDuckGo / SerpAPI |
| Crawl | httpx + Playwright |
| Extract | regex / JSON-LD + optional LLM |
| DB | MySQL, SQLAlchemy |
| Ops | Nginx, Supervisor, systemd-friendly scripts |
| Quality | pytest CI, SonarCloud |

## Архитектура (кратко)

```
keywords ──► search_keyword (SERP)
                │
                ▼
          crawl_domain (HTTP / Playwright)
                │
                ▼
        extract_contacts (regex → LLM)
                │
                ▼
             MySQL ──► Web UI / CSV export
```

Подробнее: [doc/HOW_IT_WORKS.md](doc/HOW_IT_WORKS.md) · [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## Быстрый старт (локально)

### 1. Клон и venv

```bash
git clone https://github.com/hauptmann1971/b2b-contact-miner.git
cd b2b-contact-miner
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
# source venv/bin/activate

pip install -r requirements.txt
playwright install chromium   # если нужен JS-рендер
```

### 2. Конфиг

```bash
cp .env.example .env
```

Минимум для локальной проверки:

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/contact_miner
SERP_API_PROVIDER=duckduckgo
```

Схема БД: `doc/MYSQL_SETUP.md`, миграции в `migrations/`.

### 3. Запуск

```bash
# веб-кабинет (по умолчанию http://127.0.0.1:5000)
python web_server.py

# пайплайн по pending-ключевым словам
python main.py

# опционально: health API
uvicorn monitoring.healthcheck:app --host 127.0.0.1 --port 8000
```

CLI:

```bash
python getters/add_keywords.py
python getters/view_results.py
```

## Процессы на сервере

| Процесс | Команда / unit | Порт |
|---------|----------------|------|
| Web UI | `python web_server.py` (Supervisor `b2b-web`) | `127.0.0.1:5000` → Nginx `:80` |
| Scheduler | `python scripts/scheduler.py` | — |
| Health | `uvicorn monitoring.healthcheck:app` | `127.0.0.1:8000` |
| Pipeline | `python main.py` / `scripts/run_pipeline_background.sh` | — |

Деплой: [deploy/README.md](deploy/README.md), [doc/DEPLOYMENT_GUIDE.md](doc/DEPLOYMENT_GUIDE.md).

## Структура репозитория

```
b2b-contact-miner/
├── main.py              # оркестратор пайплайна
├── web_server.py        # Flask UI
├── api_server.py        # опциональный FastAPI /health
├── services/            # SERP, crawl, extract, export
├── workers/             # MySQL task queue
├── routes/              # blueprints Flask
├── models/              # SQLAlchemy
├── templates/ + static/ # кабинет
├── scripts/             # cron, export, maintenance
├── deploy/              # nginx, start scripts
├── tests/               # pytest
└── doc/                 # документация
```

Полный индекс документов: [doc/README.md](doc/README.md).

## Тесты

```bash
pytest tests/
```

CI: `.github/workflows/tests.yml`, SonarCloud: `.github/workflows/sonarcloud.yml`.

## Кейс для портфолио / Kwork

| | |
|---|---|
| **Задача** | Собирать B2B-контакты по тематическим запросам, а не вручную гуглить сайты |
| **Решение** | Очередь задач в MySQL + SERP + crawl + extract + веб-кабинет |
| **Особенности** | Playwright при необходимости, LLM-fallback, мониторинг, Nginx + Supervisor |
| **Срок аналога «под ключ»** | от 1–2 недель в зависимости от ТЗ и источников |
| **Код** | https://github.com/hauptmann1971/b2b-contact-miner |

Типовые заказы, которые закрывает этот опыт: парсинг каталогов, мониторинг сайтов, выгрузка в Excel/Sheets, кабинет оператора, деплой на VPS.

## Лицензия

Смотри файлы репозитория; при коммерческом использовании уточняйте условия с автором.
