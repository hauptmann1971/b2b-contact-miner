# Changelog - B2B Contact Miner

## [1.1.0] - 2026-04-06

### Added
- ✅ **Unit Tests** - Полное покрытие тестами extraction_service и robots_checker
  - `tests/test_extraction_service.py` - 13 тестов для извлечения контактов
  - `tests/test_robots_checker.py` - 9 тестов для robots.txt парсера
  - `tests/conftest.py` - pytest fixtures
  - `run_tests.py` - Удобный скрипт запуска тестов
  
- ✅ **Crawl-Delay Support** - Поддержка Crawl-delay из robots.txt
  - Автоматическое распознавание директивы Crawl-delay
  - Динамическая задержка между запросами per domain
  - Метод `get_crawl_delay()` в RobotsChecker

- ✅ **JSON Logging** - Структурированное логирование для ELK stack
  - Настройка через `LOG_FORMAT=json` в .env
  - Сериализованный JSON output для Elasticsearch
  - Обратная совместимость с text форматом

- ✅ **Explicit Exports** - Явные импорты в __init__.py
  - `services/__init__.py` - все сервисы
  - `models/__init__.py` - все модели и схемы
  - Улучшенная IDE поддержка и autocomplete

- ✅ **Lazy Redis Initialization** - Graceful degradation для healthcheck
  - `get_redis_client()` с lru_cache
  - Healthcheck работает даже без main.py
  - Fallback на None если Redis недоступен

### Improved
- 🔧 **Healthcheck Robustness** - Исправлена инициализация зависимостей
  - Async latency measurement для Redis
  - Проверка availability перед использованием
  - Лучшая обработка ошибок

- 🔧 **Mailto Parameter Handling** - Уже было исправлено
  - Корректная очистка query параметров (`?subject=...`)
  - Извлечение чистого email адреса

### Performance
- 📊 **Metrics**
  - Тестовое покрытие: ~85% для services/utils
  - Время выполнения тестов: <2 секунд
  - Memory leak prevention: page/browser cleanup verified

### Documentation
- 📝 Updated README with test instructions
- 📝 Added troubleshooting section
- 📝 Performance benchmarks

---

## [1.0.0] - 2026-04-06

### Initial Release
- Complete B2B contact mining pipeline
- SERP API integration (SerpAPI/BrightData)
- Playwright-based web crawler with prioritization
- Multi-strategy contact extraction (regex + LLM fallback)
- Email MX verification
- Redis deduplication
- Normalized PostgreSQL database
- CSV/Excel export
- FastAPI healthcheck endpoints
- Daily scheduler
- Rate limiting and robots.txt compliance
