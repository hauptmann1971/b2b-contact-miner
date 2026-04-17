# ✅ Миграция на Database Task Queue - Инструкция

## Что было сделано

Созданы все необходимые файлы для замены Redis на MySQL-based task queue:

### Новые файлы:
1. ✅ `models/task_queue.py` - Модель задачи в БД
2. ✅ `workers/db_task_queue.py` - Реализация очереди задач в БД (289 строк)
3. ✅ `migrations/add_task_queue_table.sql` - SQL миграция
4. ✅ `migrations/apply_migrations.py` - Скрипт применения миграций
5. ✅ `migrations/MIGRATION_GUIDE.md` - Полная документация
6. ✅ `apply_migration.bat` - Batch файл для применения миграции

### Обновленные файлы:
1. ✅ `models/__init__.py` - Добавлен экспорт TaskQueue
2. ✅ `monitoring/healthcheck.py` - Удален Redis, добавлена поддержка DB task queue

## 📋 Следующие шаги

### 1. Примените миграцию БД
Запустите один из вариантов:

**Вариант A (простой):**
```powershell
.\apply_migration.bat
```

**Вариант B (вручную):**
```powershell
.\venv\Scripts\python.exe migrations\apply_migrations.py
```

Это создаст таблицу `task_queue` в вашей MySQL базе данных.

### 2. Обновите main.py

Найдите в файле `main.py` строки где создается task_queue и замените:

```python
# БЫЛО:
from workers.task_worker import AsyncTaskQueue
task_queue = AsyncTaskQueue(max_concurrent=20)

# СТАЛО:
from workers.db_task_queue import DatabaseTaskQueue
task_queue = DatabaseTaskQueue(max_concurrent=20)
```

Также обновите места где добавляются задачи:

```python
# БЫЛО:
await task_queue.add_task(crawl_function, arg1, arg2)

# СТАЛО:
task_id = await task_queue.add_task(
    task_name=f"Crawl {domain}",
    task_type='crawl_domain',
    payload={'domain': domain, 'keyword_id': keyword_id},
    priority=0,
    max_retries=3
)
```

### 3. Перезапустите сервисы
```powershell
.\start_all.ps1 restart
```

### 4. Проверьте health endpoint
Откройте http://localhost:8000/health

Вы должны увидеть:
```json
{
  "status": "healthy",
  "services": {
    "database": {
      "status": "healthy",
      "latency_ms": 50
    },
    "task_queue": {
      "status": "healthy",
      "type": "database",
      "pending_tasks": 0,
      "running_tasks": 0,
      "completed_tasks": 0,
      "failed_tasks": 0,
      "total_tasks": 0,
      "active_workers": 20
    }
  }
}
```

## 🎯 Преимущества новой системы

- ✅ **Персистентность** - Задачи сохраняются в БД и переживают перезапуски
- ✅ **Нет зависимостей** - Не нужен отдельный Redis сервер
- ✅ **Мониторинг** - Полная история задач с retry логикой
- ✅ **Бэкапы** - Задачи бэкапятся вместе с БД
- ✅ **Приоритеты** - Поддержка приоритетов задач
- ✅ **Планирование** - Возможность отложенного выполнения задач

## ⚠️ Важные замечания

1. **Производительность**: DB операции медленнее Redis (~50-100ms vs ~1ms), но для наших задач (минуты на crawling) это незаметно.

2. **Старые задачи**: Если у вас были задачи в in-memory очереди, они будут потеряны (это нормально - in-memory очереди не персистентны).

3. **Откат**: Если нужно вернуться к старой системе, просто удалите таблицу `task_queue` и откатите изменения кода.

## 🔧 Troubleshooting

**Ошибка при миграции:**
- Проверьте подключение к БД в `.env`
- Убедитесь что пользователь имеет права на CREATE TABLE

**Task queue показывает "not_configured":**
- Запустите миграцию: `.\apply_migration.bat`
- Проверьте логи: `.\start_all.ps1 logs monitoring`

**Workers не запускаются:**
- Проверьте что таблица создана: `SHOW TABLES LIKE 'task_queue';`
- Перезапустите сервисы: `.\start_all.ps1 restart`

## 📊 Мониторинг

Новая система предоставляет детальную статистику:
- Количество задач по статусам (pending, running, completed, failed)
- Активные воркеры
- История выполненных задач
- Retry счетчик для каждой задачи

Для просмотра статистики используйте health endpoint или добавьте API endpoint `/api/queue/stats`.

---

**Готово!** После выполнения этих шагов ваша система будет использовать надежное database-backed хранилище задач вместо Redis. 🚀
