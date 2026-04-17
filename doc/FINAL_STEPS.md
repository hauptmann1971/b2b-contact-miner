# 🚀 Завершение миграции на Database Task Queue

## ✅ Что уже сделано

Все файлы созданы и обновлены! Осталось выполнить 3 простых шага:

## 📋 Инструкция по завершению

### Шаг 1: Примените миграцию БД

**Способ A (рекомендуемый):**
```powershell
.\apply_migration.bat
```

**Способ B (вручную):**
```powershell
.\venv\Scripts\python.exe migrations\apply_migrations.py
```

Это создаст таблицу `task_queue` в MySQL.

---

### Шаг 2: Обновите main.py

Откройте файл `main.py` и найдите где создается task_queue.

**Замените:**
```python
from workers.task_worker import AsyncTaskQueue
task_queue = AsyncTaskQueue(max_concurrent=20)
```

**На:**
```python
from workers.db_task_queue import DatabaseTaskQueue
task_queue = DatabaseTaskQueue(max_concurrent=20)
```

Также обновите вызовы add_task если они есть в коде.

---

### Шаг 3: Перезапустите сервисы

```powershell
.\start_all.ps1 restart
```

---

### Шаг 4: Проверьте результат

Откройте http://localhost:8000/health

Вы должны увидеть статус `"type": "database"` для task_queue.

## 🎉 Готово!

После этих шагов ваша система будет использовать надежное database-backed хранилище задач!

## 📚 Дополнительная информация

- Полная документация: `migrations/MIGRATION_GUIDE.md`
- Краткая инструкция: `DB_TASK_QUEUE_SETUP.md`
- SQL миграция: `migrations/add_task_queue_table.sql`

## ❓ Проблемы?

Если что-то не работает:
1. Проверьте логи: `.\start_all.ps1 logs monitoring`
2. Убедитесь что таблица создана: подключитесь к MySQL и выполните `SHOW TABLES LIKE 'task_queue';`
3. Перезапустите сервисы еще раз

Удачи! 🚀
