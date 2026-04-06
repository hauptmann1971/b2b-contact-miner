# B2B Contact Miner

Автоматизированная система сбора B2B контактов для рынков СНГ и Центральной Азии.

## Возможности

✅ Автоматический перевод ключевых слов на 11+ языков  
✅ Интеграция с SERP API (SerpAPI, BrightData, ScraperAPI)  
✅ Headless browser crawling с Playwright (JavaScript rendering)  
✅ Приоритизированный обход страниц (/contact, /about, /team)  
✅ Умная фильтрация email (исключает noreply, support, free providers)  
✅ Извлечение Telegram и LinkedIn профилей  
✅ LLM fallback для обфусцированных email  
✅ MX verification для проверки email  
✅ Redis дедупликация доменов (TTL 30 дней)  
✅ Rate limiting per domain (Semaphore)  
✅ Robots.txt проверка  
✅ Sitemap парсинг для быстрого поиска контактов  
✅ Нормализованная БД с эффективными индексами  
✅ Экспорт в CSV/Excel с фильтрацией  
✅ Healthcheck API для мониторинга  
✅ Ежедневный запуск по расписанию  

## Установка

### 1. Зависимости

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Тесты

```bash
# Запустить все тесты
python run_tests.py

# Или напрямую через pytest
pytest tests/ -v

# С покрытием кода
pytest tests/ --cov=services --cov=utils --cov-report=html
```

### 3. База данных

Установите PostgreSQL и создайте базу:

```sql
CREATE DATABASE contact_miner;
CREATE USER miner WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE contact_miner TO miner;
```

### 4. Redis

```bash
# Windows (через WSL или Docker)
docker run -d -p 6379:6379 redis:7-alpine

# Linux
sudo apt-get install redis-server
sudo systemctl start redis
```

### 5. Конфигурация

```bash
cp .env.example .env
# Отредактируйте .env с вашими API ключами
```

### 6. Инициализация БД

```bash
python -c "from models.database import init_db; init_db()"
```

## Использование

### Добавление ключевых слов

```python
from models.database import SessionLocal
from services.keyword_service import KeywordService
from models.schemas import KeywordInput

db = SessionLocal()
service = KeywordService(db)

# Добавить ключевое слово
keyword = service.add_keyword(KeywordInput(
    keyword="финтех стартап",
    language="ru",
    country="RU"
))

# Сгенерировать переводы
translations = service.generate_translations("финтех стартап", "ru")
for lang, variants in translations.items():
    for variant in variants:
        service.add_keyword(KeywordInput(
            keyword=variant,
            language=lang,
            country="RU"
        ))
```

### Запуск пайплайна вручную

```bash
python main.py
```

### Запуск планировщика (ежедневно в 02:00)

```bash
python scheduler.py
```

### Запуск API сервера

```bash
python api_server.py
```

API будет доступен на http://localhost:8000

### Экспорт данных

```bash
# CSV экспорт
curl http://localhost:8000/export/csv?min_confidence=50 -o contacts.csv

# Excel экспорт
curl http://localhost:8000/export/excel -o contacts.xlsx

# Статистика
curl http://localhost:8000/export/summary
```

### Healthcheck

```bash
# Проверка здоровья системы
curl http://localhost:8000/health/health

# Readiness probe (Kubernetes)
curl http://localhost:8000/health/ready

# Liveness probe (Kubernetes)
curl http://localhost:8000/health/live

# Метрики пайплайна
curl http://localhost:8000/health/metrics/pipeline
```

## Архитектура

```
b2b-contact-miner/
├── config/              # Конфигурация
│   ├── settings.py      # Настройки из .env
├── models/              # Модели данных
│   ├── database.py      # SQLAlchemy модели
│   └── schemas.py       # Pydantic схемы
├── services/            # Бизнес-логика
│   ├── keyword_service.py       # Управление ключевыми словами
│   ├── translation_service.py   # Перевод关键词
│   ├── serp_service.py          # SERP API интеграция
│   ├── crawler_service.py       # Web crawler с Playwright
│   ├── extraction_service.py    # Извлечение контактов
│   └── export_service.py        # Экспорт CSV/Excel
├── utils/               # Утилиты
│   ├── state_manager.py         # Мониторинг прогресса
│   └── robots_checker.py        # Проверка robots.txt
├── workers/             # Асинхронные задачи
│   └── task_worker.py           # AsyncTaskQueue
├── monitoring/          # Мониторинг
│   └── healthcheck.py           # Healthcheck API
├── main.py              # Главный пайплайн
├── scheduler.py         # Планировщик
└── api_server.py        # REST API
```

## Пайплайн обработки

1. **Keyword Management** - Ввод keywords, перевод, дедупликация
2. **SERP Search** - Поиск через SerpAPI/BrightData
3. **Web Crawling** - Playwright headless browser
   - Проверка robots.txt
   - Парсинг sitemap.xml
   - Приоритизированный обход (priority 1-10)
   - Rate limiting per domain (Semaphore)
   - Ротация User-Agent
4. **Contact Extraction** - Multi-strategy
   - Regex extraction (email, Telegram, LinkedIn)
   - Mailto link parsing
   - Obfuscation detection
   - LLM fallback (только для /contact с обфускацией)
   - MX verification
5. **Data Storage** - PostgreSQL с нормализацией
6. **Export** - CSV/Excel с фильтрацией

## Ключевые особенности

### Приоритизация страниц

```
Priority 10: /contact, /contacts, /contact-us
Priority 9:  /about, /about-us, /company
Priority 8:  /team, /our-team, /leadership
Priority 7:  Homepage
Priority 6:  /impressum, /legal, /privacy
Priority 5:  Team variations
Priority 4:  /services, /products
Priority 2:  /blog, /news
Priority 1:  Everything else
```

### Email фильтрация

Блокируются:
- noreply@, no-reply@, donotreply@
- support@, info@, admin@, webmaster@, postmaster@
- Free providers: gmail.com, yahoo.com, mail.ru, yandex.ru

### LLM Fallback

Используется ТОЛЬКО когда:
- Страница типа /contact или /about
- Обнаружена обфускация ([at], (at), name [at] domain)
- Regex не нашёл ≥2 email

Экономия: ~$15-18 за прогон vs наивный подход

### Rate Limiting

- DELAY_BETWEEN_REQUESTS: 1.0s между запросами
- Semaphore(5): максимум 5 одновременных запросов к одному домену
- MAX_CONCURRENT_DOMAINS: 20 параллельных доменов

## Производительность

- Обработка: 500-1000 сайтов за прогон
- Время выполнения: 2-4 часа
- Память: ~4GB (Playwright browsers)
- Стоимость SERP API: ~$5-10 за 1000 поисков

## Мониторинг

Прогресс сохраняется в БД после каждого keyword. Если пайплайн упал:

```python
from utils.state_manager import StateManager

sm = StateManager()
status = sm.get_last_run_status()
print(status)
# {
#   "run_id": "a3f2b1c4",
#   "total_keywords": 50,
#   "completed": 35,
#   "failed": 2,
#   "processing": 13,
#   "total_contacts": 1247,
#   "overall_progress": 70
# }
```

## Docker (опционально)

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: contact_miner
      POSTGRES_USER: miner
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  crawler:
    build: .
    environment:
      - DATABASE_URL=postgresql://miner:${DB_PASSWORD}@postgres:5432/contact_miner
      - REDIS_URL=redis://redis:6379/0
      - SERPAPI_KEY=${SERPAPI_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs

volumes:
  postgres_data:
  redis_data:
```

## Troubleshooting

### Playwright не запускается

```bash
playwright install --with-deps chromium
```

### Ошибка подключения к Redis

Проверьте, что Redis запущен:
```bash
redis-cli ping
# Должен ответить: PONG
```

### SERP API лимиты

SerpAPI free tier: 100 searches/month  
Для продакшена нужен paid plan (~$50/month для 5000 searches)

### Медленная обработка

Увеличьте параллелизм:
```python
# В .env
MAX_CONCURRENT_DOMAINS=30
MAX_CONCURRENT_DOMAINS_PER_SITE=8
```

## Лицензия

MIT
