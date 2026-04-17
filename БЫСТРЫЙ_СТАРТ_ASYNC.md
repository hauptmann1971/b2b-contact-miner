# Быстрый старт - Async Parallel Pipeline

## 🚀 Запуск новой системы

### Шаг 1: Применить миграцию БД

```bash
python migrations/apply_task_queue_dependency_migration.py
```

Ожидаемый вывод:
```
✓ Added keyword_id column
✓ Added depends_on_task_id column
✓ Created index on keyword_id
✓ Created index on depends_on_task_id
✅ Migration completed successfully!
```

### Шаг 2: Запустить тест (опционально)

```bash
python test_async_pipeline.py
```

Это проверит всю систему на одном ключевом слове.

### Шаг 3: Запустить основной пайплайн

```bash
python main.py
```

Или использовать скрипт запуска:
```bash
# Windows
start_all.bat start

# Linux/Mac
./start_all.sh start
```

### Шаг 4: Мониторинг прогресса

**В терминале:**
- Логи показывают статистику очереди каждые 30 секунд
- Формат: `📊 Queue: X pending | Y running | Z completed | W failed`

**Через API:**
```bash
curl http://localhost:8000/metrics/pipeline
```

**Через браузер:**
- http://localhost:5000/health-check - визуальный интерфейс
- http://localhost:8000/docs - FastAPI документация

---

## 📊 Что изменилось?

### Было (старая версия):
```
Keyword 1 → Search → Crawl → Extract → Save (2 мин)
Keyword 2 → Search → Crawl → Extract → Save (2 мин)  
Keyword 3 → Search → Crawl → Extract → Save (2 мин)
Итого: 6 минут
```

### Стало (новая версия):
```
Все keywords обрабатываются ПАРАЛЛЕЛЬНО через очередь задач:
- Worker 1: Search Keyword 1
- Worker 2: Crawl site1.com (из Keyword 1)
- Worker 3: Crawl site2.com (из Keyword 2) ← ПАРАЛЛЕЛЬНО!
- Worker 4: Extract contacts (из site3.com) ← ПАРАЛЛЕЛЬНО!
Итого: 1-2 минуты (в 3-6 раз быстрее!)
```

---

## 🔧 Настройка производительности

Отредактируйте `.env`:

```bash
# Количество параллельных workers (по умолчанию 20)
MAX_CONCURRENT_DOMAINS=20

# Retries для разных типов задач
SEARCH_MAX_RETRIES=3
CRAWL_MAX_RETRIES=2
EXTRACT_MAX_RETRIES=1
SAVE_MAX_RETRIES=3

# Timeout для stale задач (секунды)
TASK_LOCK_TIMEOUT=300
```

Перезапустите после изменений:
```bash
./start_all.sh restart
```

---

## ❓ Troubleshooting

### Задачи не выполняются

**Проверить статус очереди:**
```python
python -c "
import asyncio
from workers.db_task_queue import DatabaseTaskQueue

async def check():
    q = DatabaseTaskQueue()
    stats = await q.get_queue_stats()
    print(stats)

asyncio.run(check())
"
```

**Ожидаемый результат:**
```python
{
  'pending': 10,      # Задачи в очереди
  'running': 5,       # Сейчас выполняются (должно быть > 0)
  'completed': 20,    #已完成
  'failed': 1,        # Ошибки
  'total': 36,
  'current_workers': 5,  # Активные workers
  'keywords_in_progress': 3
}
```

Если `running: 0` и `pending > 0` - workers не запущены!

### Stale задачи (зависшие)

Автоматически восстанавливаются при следующем запуске.

Или вручную:
```python
python -c "
import asyncio
from workers.db_task_queue import DatabaseTaskQueue

async def recover():
    q = DatabaseTaskQueue()
    recovered = await q.recover_stale_tasks()
    print(f'Recovered {recovered} tasks')

asyncio.run(recover())
"
```

### Очистка старых задач

```python
python -c "
import asyncio
from workers.db_task_queue import DatabaseTaskQueue

async def clear():
    q = DatabaseTaskQueue()
    deleted = await q.clear_completed_tasks(older_than_days=7)
    print(f'Deleted {deleted} old tasks')

asyncio.run(clear())
"
```

---

## 📈 Сравнение производительности

| Метрика | Старая версия | Новая версия | Улучшение |
|---------|--------------|--------------|-----------|
| 10 keywords | ~20 мин | ~2-3 мин | **6-10x** |
| 50 keywords | ~100 мин | ~5-10 мин | **10-20x** |
| CPU usage | Низкий | Высокий | Лучше утилизация |
| Fault tolerance | Низкая | Высокая | Отказоустойчивость |

---

## ✅ Проверка успешности

После завершения пайплайна проверьте результаты:

```python
python -c "
from models.database import SessionLocal, Keyword, DomainContact, Contact

db = SessionLocal()

# Проверить processed keywords
processed = db.query(Keyword).filter(Keyword.is_processed == True).count()
print(f'Processed keywords: {processed}')

# Проверить найденные контакты
domains = db.query(DomainContact).count()
contacts = db.query(Contact).count()
print(f'Domains with contacts: {domains}')
print(f'Total contacts: {contacts}')

db.close()
"
```

---

## 🎯 Главное

1. ✅ Применить миграцию БД
2. ✅ Запустить `python main.py`
3. ✅ Наблюдать за прогрессом в логах
4. ✅ Проверить результаты в БД

**Всё готово! Наслаждайтесь скоростью! 🚀**
