# 📚 Документация B2B Contact Miner

Эта папка содержит всю документацию проекта.

## 📖 Основные документы

### Архитектура и дизайн
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Полная архитектура системы, взаимодействие модулей
- **[DIAGRAMS.md](DIAGRAMS.md)** - Визуальные диаграммы (Mermaid)
- **[HOW_IT_WORKS.md](HOW_IT_WORKS.md)** - Простое объяснение работы проекта

### Настройка и установка
- **[REDIS_SETUP.md](REDIS_SETUP.md)** - Установка и настройка Redis на Windows
- **[DOCKER_SETUP.md](DOCKER_SETUP.md)** - Docker конфигурация и инструкции
  - `docker-compose.yml` - Конфигурация для запуска Redis и MySQL
- **[MYSQL_SETUP.md](MYSQL_SETUP.md)** - Настройка MySQL базы данных
- **[INSTALL_DEPS.md](INSTALL_DEPS.md)** - Установка зависимостей
- **[API_KEYS_SETUP.md](API_KEYS_SETUP.md)** - Настройка API ключей

### LLM интеграции
- **[YANDEXGPT_SETUP.md](YANDEXGPT_SETUP.md)** - Настройка YandexGPT
- **[GIGACHAT_SETUP.md](GIGACHAT_SETUP.md)** - Настройка GigaChat (Sber)
- **[FIX_YANDEXGPT_403.md](FIX_YANDEXGPT_403.md)** - Исправление ошибок YandexGPT

### Руководства пользователя
- **[KEYWORDS_GUIDE.md](KEYWORDS_GUIDE.md)** - Как добавлять и управлять ключевыми словами
- **[RUN_TESTS_GUIDE.md](RUN_TESTS_GUIDE.md)** - Запуск тестов
- **[RELIABILITY_IMPROVEMENTS.md](RELIABILITY_IMPROVEMENTS.md)** - Улучшения надежности пайплайна

### Отчеты и changelog
- **[README.md](README.md)** - Основная документация проекта
- **[CHANGELOG.md](CHANGELOG.md)** - История изменений
- **[TEST_REPORT.md](TEST_REPORT.md)** - Отчеты о тестировании

## 🗄️ Конфигурационные файлы

- **`setup_mysql.sql`** - SQL скрипт для инициализации базы данных
- **`docker-compose.yml`** - Docker Compose конфигурация для Redis и MySQL

## 📝 Структура документации

```
doc/
├── ARCHITECTURE.md              # Архитектура системы
├── DIAGRAMS.md                  # Диаграммы
├── HOW_IT_WORKS.md             # Как работает проект
├── REDIS_SETUP.md              # Настройка Redis
├── DOCKER_SETUP.md             # Docker setup
├── MYSQL_SETUP.md              # Настройка MySQL
├── INSTALL_DEPS.md             # Установка зависимостей
├── API_KEYS_SETUP.md           # API ключи
├── YANDEXGPT_SETUP.md          # YandexGPT настройка
├── GIGACHAT_SETUP.md           # GigaChat настройка
├── FIX_YANDEXGPT_403.md        # Исправление ошибок
├── KEYWORDS_GUIDE.md           # Работа с ключевыми словами
├── RUN_TESTS_GUIDE.md          # Тестирование
├── RELIABILITY_IMPROVEMENTS.md # Надежность
├── README.md                   # Главная документация
├── CHANGELOG.md                # История изменений
├── TEST_REPORT.md              # Отчеты тестов
├── docker-compose.yml          # Docker конфигурация
└── setup_mysql.sql             # SQL инициализация
```

## 🔗 Быстрые ссылки

- [Начало работы →](README.md)
- [Архитектура →](ARCHITECTURE.md)
- [Docker Setup →](DOCKER_SETUP.md)
- [Redis Setup →](REDIS_SETUP.md)
- [Как работает →](HOW_IT_WORKS.md)
