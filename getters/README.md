# 📥 Getters - Скрипты получения данных и утилиты

Эта папка содержит скрипты для получения данных, токенов и управления информацией.

## 📋 Доступные скрипты

### Управление ключевыми словами
- **`add_keywords.py`** - Добавление ключевых слов в базу данных
  ```bash
  # Добавить примеры ключевых слов
  python getters/add_keywords.py
  
  # Показать существующие ключи
  python getters/add_keywords.py show
  ```

### Получение токенов и credentials
- **`get_iam_from_oauth.py`** - Получение IAM токена из OAuth токена (Yandex)
- **`get_iam_token.py`** - Получение IAM токена из API ключа
- **`get_iam_token_simple.py`** - Упрощенное получение IAM токена
- **`update_iam_token.py`** - Обновление IAM токена в .env
- **`setup_yandex_credentials.py`** - Настройка credentials Yandex Cloud

### Просмотр результатов
- **`view_results.py`** - Просмотр результатов краулинга из БД
  ```bash
  python getters/view_results.py
  ```
  
- **`check_db_raw.py`** - Проверка сырых данных в таблицах БД
  ```bash
  python getters/check_db_raw.py
  ```

## 🚀 Использование

### Работа с ключевыми словами:
```bash
# Добавить ключевые слова
python getters/add_keywords.py

# Посмотреть результаты
python getters/view_results.py
```

### Получение токенов:
```bash
# Получить IAM токен из OAuth
python getters/get_iam_from_oauth.py

# Обновить токен в .env
python getters/update_iam_token.py
```

### Анализ данных:
```bash
# Проверить БД
python getters/check_db_raw.py
```

## 📊 Вывод скриптов

### add_keywords.py
```
✅ Added keyword: 'финтех стартап' (ID: 1)
✅ Added keyword: 'AI компания Москва' (ID: 2)
...
```

### view_results.py
```
================================================================================
Keyword: 'финтех стартап' (ru, RU)
Status: ✅ Processed | Last crawled: 2026-04-09 15:40

🌐 Domains Crawled: 2
   📍 mkechinov.ru
      • email: info@mkechinov.ru
   📍 rb.ru
      • email: team@rb.ru

Total contacts: 2 emails
================================================================================
```

## 🔧 Добавление новых скриптов

При создании нового getter'а:
1. Используйте понятное имя (get_*, view_*, check_*, add_*)
2. Добавьте документацию в начало файла
3. Поддерживайте аргументы командной строки
4. Обновите этот README
