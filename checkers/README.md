# 🔍 Checkers - Скрипты проверки и тестирования

Эта папка содержит скрипты для проверки работоспособности компонентов системы.

## 📋 Доступные чекеры

### Docker и инфраструктура
- **`check_docker.py`** - Проверка установки Docker, Docker daemon и docker-compose
  ```bash
  python checkers/check_docker.py
  ```

### API и сервисы
- **`test_deepseek.py`** - Тестирование DeepSeek API
- **`test_deepseek_simple.py`** - Упрощенный тест DeepSeek
- **`test_yandexgpt.py`** - Тестирование YandexGPT API
- **`test_duckduckgo.py`** - Тестирование поиска DuckDuckGo

### База данных
- **`test_mysql_connection.py`** - Проверка подключения к MySQL
- **`test_regex.py`** - Тестирование regex паттернов

### Пайплайн
- **`test_manual.py`** - Ручное тестирование пайплайна
- **`test_single_keyword.py`** - Тест с одним ключевым словом
- **`test_single_keyword_reliable.py`** - Тест с улучшенной обработкой ошибок
- **`smoke_pipeline_quality.py`** - Быстрый smoke-бенчмарк качества crawl/extract на 10-20 доменах
  ```bash
  # Без записи в БД (безопасный режим по умолчанию)
  py checkers/smoke_pipeline_quality.py --limit 10

  # С записью в БД (crawl_logs/domain_contacts/contacts)
  py checkers/smoke_pipeline_quality.py --limit 10 --write-db

  # Явно указать путь для JSON-отчета
  py checkers/smoke_pipeline_quality.py --limit 10 --report-file artifacts/smoke-reports/latest.json
  ```
  По умолчанию JSON-отчет сохраняется автоматически в `artifacts/smoke-reports/`.
- **`compare_smoke_reports.py`** - Сравнение двух smoke JSON-отчетов (дельты KPI)
  ```bash
  # Сравнить 2 последних отчета из artifacts/smoke-reports/
  py checkers/compare_smoke_reports.py

  # Сравнить конкретные отчеты
  py checkers/compare_smoke_reports.py --new artifacts/smoke-reports/new.json --old artifacts/smoke-reports/old.json
  ```
- **`run_weekly_smoke.py`** - Запустить smoke и сразу сравнить с предыдущим отчетом
  ```bash
  # Weekly smoke (без записи в БД)
  py checkers/run_weekly_smoke.py --limit 15

  # Weekly smoke с записью в БД
  py checkers/run_weekly_smoke.py --limit 15 --write-db
  ```

## 🚀 Использование

### Проверить всё сразу:
```bash
# Проверить Docker
python checkers/check_docker.py

# Проверить MySQL
python checkers/test_mysql_connection.py

# Проверить LLM API
python checkers/test_yandexgpt.py
```

### Запустить все тесты:
```bash
python run_tests.py
```

## 📊 Результаты

Каждый чекер выводит:
- ✅ Успешные проверки
- ❌ Ошибки и проблемы
- 💡 Рекомендации по исправлению

## 🔧 Добавление новых чекеров

При создании нового чекера:
1. Используйте префикс `test_` или `check_`
2. Добавьте документацию в начало файла
3. Обновите этот README
