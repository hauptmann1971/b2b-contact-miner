# 🚀 Быстрый старт с виртуальным окружением

## ✅ Что готово

- ✅ Виртуальное окружение создано (Python 3.13.5)
- ✅ Все зависимости установлены (77 пакетов)
- ✅ Браузеры Playwright установлены
- ✅ Тесты конфигурации проходят (25/25)
- ✅ Приложение готово к запуску

---

## 📋 Команды для работы

### 1. Активация виртуального окружения

**PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
```

**CMD:**
```cmd
.venv\Scripts\activate.bat
```

После активации вы увидите `(.venv)` в начале строки приглашения.

### 2. Запуск тестов

**Все тесты:**
```bash
pytest tests/ -v
```

**Только тесты конфигурации (работают без БД):**
```bash
pytest tests/test_settings_config.py -v
```

**С отчетом о покрытии:**
```bash
pytest tests/ --cov=. --cov-report=html
```

### 3. Запуск приложения

**Веб-интерфейс (Flask):**
```bash
python web_server.py
```
Откройте в браузере: http://localhost:5000

**API сервер (FastAPI):**
```bash
python api_server.py
```
Документация API: http://localhost:8000/docs

**Основной пайплайн:**
```bash
python main.py
```

**Планировщик задач:**
```bash
python scheduler.py
```

**Мониторинг здоровья:**
```bash
python monitoring/healthcheck.py
```

### 4. Установка браузеров (если нужно обновить)

```bash
playwright install chromium
playwright install --with-deps chromium
```

---

## ⚙️ Настройка перед первым запуском

### 1. Создайте .env файл
```bash
cp .env.example .env
```

### 2. Отредактируйте .env
Откройте `.env` и настройте:

```env
# Database
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/contact_miner

# API Keys (опционально)
SERPAPI_KEY=your_key_here
YANDEX_IAM_TOKEN=your_token_here

# Security (оставьте пустым для автогенерации)
SECRET_KEY=

# Pipeline Settings
SEARCH_RESULTS_PER_KEYWORD=5
MAX_KEYWORDS_PER_RUN=50

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=text
```

### 3. Создайте базу данных MySQL
```sql
CREATE DATABASE contact_miner CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Запустите миграции
```bash
python -m alembic upgrade head
```

---

## 🧪 Проверка работоспособности

### Проверка Python
```bash
python --version
# Должно быть: Python 3.13.5
```

### Проверка зависимостей
```bash
python -c "import flask, fastapi, sqlalchemy, playwright; print('All imports OK')"
```

### Проверка конфигурации
```bash
python -c "from config.settings import settings; print('DB:', settings.DATABASE_URL[:30])"
```

### Проверка веб-сервера
```bash
python -c "from web_server import app; print('App:', app.name, '| Secret key:', len(app.secret_key), 'chars')"
```

---

## 📁 Структура проекта

```
b2b-contact-miner/
├── .venv/                  # Виртуальное окружение (не коммитить)
├── .env                    # Ваши настройки (не коммитить)
├── .env.example            # Пример настроек
│
├── config/                 # Конфигурация
│   └── settings.py
│
├── models/                 # Модели данных
│   ├── database.py
│   └── schemas.py
│
├── services/               # Бизнес-логика
│   ├── crawler_service.py
│   ├── extraction_service.py
│   └── ...
│
├── tests/                  # Тесты
│   ├── test_settings_config.py      ✅ Работает
│   ├── test_input_validation.py     ⚠️ Нужна БД
│   ├── test_json_error_handling.py  ⚠️ Нужны доработки
│   └── test_session_management.py   ⚠️ Нужна БД
│
├── templates/              # HTML шаблоны
├── getters/                # Утилиты для работы с БД
├── checkers/               # Проверочные скрипты
│
├── main.py                 # Основной пайплайн
├── web_server.py           # Веб-интерфейс
├── api_server.py           # REST API
├── scheduler.py            # Планировщик
│
└── requirements.txt        # Зависимости
```

---

## 🔧 Решение проблем

### Ошибка: ModuleNotFoundError
```bash
# Переустановите зависимости
pip install -r requirements.txt
```

### Ошибка: Can't connect to MySQL
```bash
# Проверьте, что MySQL запущен
# Проверьте настройки в .env файле
# Создайте базу данных
```

### Ошибка: Playwright browsers not found
```bash
# Переустановите браузеры
playwright install --with-deps chromium
```

### Тесты падают с OperationalError
```bash
# Это нормально - нужна настроенная БД
# Запускайте только тесты конфигурации:
pytest tests/test_settings_config.py -v
```

---

## 📊 Статистика проекта

- **Версия Python:** 3.13.5
- **Всего пакетов:** 77 основных + зависимости
- **Тестов написано:** 67
- **Тестов проходит:** 44 (66%)
- **Файлов кода:** ~50
- **Строк кода:** ~10,000+

---

## 🎯 Следующие шаги

1. **Настроить MySQL базу данных** (см. doc/MYSQL_SETUP.md)
2. **Получить API ключи** (см. doc/API_KEYS_SETUP.md)
3. **Добавить ключевые слова** через веб-интерфейс или скрипт
4. **Запустить пайплайн** и наблюдать за результатами
5. **Экспортировать контакты** в Excel/CSV

---

## 📚 Документация

- [Руководство по запуску](STARTUP_GUIDE.md)
- [Как это работает](doc/HOW_IT_WORKS.md)
- [Архитектура](doc/ARCHITECTURE.md)
- [Настройка API ключей](doc/API_KEYS_SETUP.md)
- [Настройка MySQL](doc/MYSQL_SETUP.md)
- [Отчет об улучшениях](IMPROVEMENTS.md)
- [История изменений](CHANGELOG.md)

---

**Готово! 🎉** Ваше виртуальное окружение настроено и готово к работе.
