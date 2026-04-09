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
- **`test_gigachat.py`** - Тестирование GigaChat API
- **`test_gigachat_auth.py`** - Проверка аутентификации GigaChat
- **`test_yandexgpt.py`** - Тестирование YandexGPT API
- **`test_duckduckgo.py`** - Тестирование поиска DuckDuckGo

### База данных
- **`test_mysql_connection.py`** - Проверка подключения к MySQL
- **`test_regex.py`** - Тестирование regex паттернов

### Пайплайн
- **`test_manual.py`** - Ручное тестирование пайплайна
- **`test_single_keyword.py`** - Тест с одним ключевым словом
- **`test_single_keyword_reliable.py`** - Тест с улучшенной обработкой ошибок

## 🚀 Использование

### Проверить всё сразу:
```bash
# Проверить Docker
python checkers/check_docker.py

# Проверить MySQL
python checkers/test_mysql_connection.py

# Проверить LLM API
python checkers/test_yandexgpt.py
python checkers/test_gigachat.py
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
