# 🔍 Мониторинг воркеров и очереди задач

## Как понять, работает ли воркер или завис?

Система предоставляет несколько способов мониторинга состояния воркеров и задач.

---

## 📊 1. Мониторинг через скрипт (Рекомендуемый способ)

### Запуск мониторинга

```bash
python monitor_workers.py
```

### Что показывает:

#### ✅ Статистика задач
```
📊 СТАТИСТИКА ЗАДАЧ:
--------------------------------------------------------------------------------      
   ✅ completed   :  216 ( 96.0%)
   ❌ failed      :    9 (  4.0%)
   ========================================
   ВСЕГО       :  225
```

**Как интерпретировать:**
- `completed` - успешно выполненные задачи ✅
- `failed` - упавшие с ошибкой ❌
- `pending` - ожидают выполнения ⏳
- `running` - выполняются сейчас 🔄

#### 🚨 Зависшие задачи (Stale Tasks)

```
🚨 ЗАВИСШИЕ ЗАДАЧИ (stale tasks):
--------------------------------------------------------------------------------      
   ✅ Нет зависших задач
```

**Что такое stale task:**
- Задача в статусе `running`, которая выполняется дольше `TASK_LOCK_TIMEOUT` (по умолчанию 300 секунд = 5 минут)
- Обычно это означает, что воркер упал или завис
- Система автоматически восстанавливает такие задачи при следующем запуске pipeline

**Если найдены зависшие задачи:**
```
⚠️  НАЙДЕНО 3 ЗАВИСШИХ ЗАДАЧ!
💡 Запустите: python recover_stale_tasks.py
```

#### 🔄 Активные задачи

```
🔄 АКТИВНЫЕ ЗАДАЧИ (выполняются сейчас):
--------------------------------------------------------------------------------      
   🔄 Task #245: crawl_domain         (2.3 min)
       Domain: example.com
   🔄 Task #246: extract_contacts     (0.5 min)
       Domain: test.ru
```

**Как интерпретировать:**
- Показывает задачи, которые выполняются прямо сейчас
- Время выполнения помогает выявить "зависшие" задачи
- Нормальное время:
  - `search_keyword`: 1-5 секунд
  - `crawl_domain`: 10-60 секунд
  - `extract_contacts`: 5-30 секунд

**Признаки проблемы:**
- Задача выполняется > 5 минут → возможно зависла
- Много задач с одинаковым доменом → возможно rate limiting

#### ❌ Последние ошибки

```
❌ ПОСЛЕДНИЕ ОШИБКИ:
--------------------------------------------------------------------------------      
   ❌ Task #95: search_keyword
       Error: RetryError[ModuleNotFoundError]
       Time: 2026-04-19 18:31:59
```

**Что делать:**
- Посмотреть полный текст ошибки в логах
- Проверить, установлены ли все зависимости
- Если ошибка повторяется для многих задач → системная проблема

#### 📝 Прогресс по ключевым словам

```
📝 ПРОГРЕСС ПО КЛЮЧЕВЫМ СЛОВАМ:
--------------------------------------------------------------------------------      
   ✅ искусственный интеллект        | Search Results: 19
   ✅ KI startup München             | Search Results: 16
   ✅ fintech unternehmen            | Search Results: 11
```

**Как интерпретировать:**
- `✅` - keyword полностью обработан
- `⏳` - keyword ещё не начал обрабатываться
- `Search Results` - количество найденных доменов

---

## 🛠️ 2. Восстановление зависших задач

### Автоматическое восстановление

При запуске pipeline система **автоматически** проверяет и восстанавливает зависшие задачи:

```python
# В workers/db_task_queue.py:start_workers()
recovered = await self.recover_stale_tasks()
if recovered > 0:
    logger.info(f"Recovered {recovered} stale tasks before starting workers")
```

### Ручное восстановление

Если pipeline не запущен, но есть зависшие задачи:

```bash
python recover_stale_tasks.py
```

**Результат:**
```
================================================================================
✅ Восстановлено 3 зависших задач
   Задачи возвращены в очередь pending и будут обработаны
================================================================================
```

**Что происходит:**
1. Находятся все задачи со статусом `running`
2. Проверяется время блокировки (`locked_at`)
3. Если задача заблокирована дольше `TASK_LOCK_TIMEOUT` (5 минут) → статус меняется на `pending`
4. При следующем запуске pipeline задача будет выполнена заново

---

## 🌐 3. Мониторинг через веб-интерфейс

### Запуск Flask сервера

```bash
# Windows
start_all.bat

# Linux/Mac
./start_all.sh
```

Веб-интерфейс доступен по адресу: `http://localhost:5000`

**Что показывает:**
- Общее количество контактов
- Распределение по типам (email, telegram, linkedin, phone)
- Последние добавленные keywords
- Статистика по domain_contacts

---

## 📋 4. Быстрая проверка через SQL

### Подключиться к БД

```bash
mysql -u b2b_user -p b2b_contact_miner
```

### Проверить статус задач

```sql
-- Общая статистика
SELECT status, COUNT(*) as count 
FROM task_queue 
GROUP BY status;

-- Зависшие задачи (running > 5 минут)
SELECT id, task_type, locked_at, 
       TIMESTAMPDIFF(MINUTE, locked_at, NOW()) as minutes_running
FROM task_queue
WHERE status = 'running'
  AND locked_at < NOW() - INTERVAL 5 MINUTE;

-- Активные задачи
SELECT id, task_type, payload, locked_at
FROM task_queue
WHERE status = 'running'
ORDER BY locked_at DESC
LIMIT 10;

-- Последние ошибки
SELECT id, task_type, error_message, created_at
FROM task_queue
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 5;
```

---

## 🎯 Признаки проблем и решения

### Проблема 1: Воркер завис

**Признаки:**
- Задача в статусе `running` > 5 минут
- В логах нет активности от этого воркера
- `monitor_workers.py` показывает stale tasks

**Решение:**
```bash
# 1. Восстановить зависшие задачи
python recover_stale_tasks.py

# 2. Перезапустить pipeline
python main.py
```

### Проблема 2: Много ошибок

**Признаки:**
- `failed` задач > 10% от общего числа
- Одинаковые ошибки в логах

**Решение:**
```bash
# 1. Посмотреть детали ошибок
python monitor_workers.py

# 2. Проверить логи
tail -f logs/pipeline.log  # Linux
Get-Content logs/pipeline.log -Wait  # Windows

# 3. Исправить причину и перезапустить
```

### Проблема 3: Pipeline не запускается

**Признаки:**
- Ошибки при старте
- Workers не запускаются

**Решение:**
```bash
# 1. Проверить подключение к БД
python check_contacts.py

# 2. Проверить настройки
cat .env  # Linux
type .env  # Windows

# 3. Убедиться, что MySQL запущен
# Windows: Services -> MySQL
# Linux: systemctl status mysql
```

### Проблема 4: Задачи не выполняются

**Признаки:**
- Все задачи в статусе `pending`
- Нет активных задач
- Pipeline запущен, но ничего не происходит

**Решение:**
```bash
# 1. Проверить, запущены ли workers
python monitor_workers.py

# 2. Посмотреть логи workers
# Искать сообщения о старте workers:
# "Started 20 database-backed workers"

# 3. Перезапустить pipeline
Ctrl+C  # остановить
python main.py  # запустить заново
```

---

## ⚙️ Настройки мониторинга

### TASK_LOCK_TIMEOUT

В `.env` файле:

```env
# Timeout для stale задач (секунды)
TASK_LOCK_TIMEOUT=300
```

**Рекомендации:**
- `300` (5 минут) - для обычных сайтов
- `600` (10 минут) - для медленных сайтов
- `120` (2 минуты) - для быстрых проверок

**После изменения нужно перезапустить pipeline!**

---

## 📊 Примеры использования

### Пример 1: Проверка перед запуском нового keyword

```bash
# 1. Проверить текущее состояние
python monitor_workers.py

# 2. Убедиться, что нет зависших задач
# Если есть → восстановить
python recover_stale_tasks.py

# 3. Добавить новый keyword через веб-интерфейс
# http://localhost:5000

# 4. Запустить pipeline
python main.py
```

### Пример 2: Диагностика проблем

```bash
# 1. Посмотреть статистику
python monitor_workers.py

# 2. Если много ошибок → посмотреть детали
mysql -u b2b_user -p b2b_contact_miner -e "
  SELECT task_type, error_message, COUNT(*) 
  FROM task_queue 
  WHERE status = 'failed' 
  GROUP BY task_type, LEFT(error_message, 100);
"

# 3. Проверить логи
grep "ERROR" logs/pipeline.log | tail -20
```

### Пример 3: Мониторинг во время работы

```bash
# В одном терминале запустить pipeline
python main.py

# В другом терминале периодически проверять статус
watch -n 10 python monitor_workers.py  # Linux
# Или вручную каждые 10 секунд
python monitor_workers.py
```

---

## 🔧 API для разработчиков

### Программная проверка stale tasks

```python
import asyncio
from workers.db_task_queue import DatabaseTaskQueue

async def check_stale():
    queue = DatabaseTaskQueue()
    recovered = await queue.recover_stale_tasks()
    
    if recovered > 0:
        print(f"Recovered {recovered} stale tasks")
    else:
        print("No stale tasks found")

asyncio.run(check_stale())
```

### Проверка статуса очереди

```python
from models.database import SessionLocal
from models.task_queue import TaskQueue
from sqlalchemy import func

db = SessionLocal()

# Статистика
stats = db.query(
    TaskQueue.status,
    func.count(TaskQueue.id)
).group_by(TaskQueue.status).all()

for status, count in stats:
    print(f"{status}: {count}")

db.close()
```

---

## 💡 Best Practices

1. **Перед запуском pipeline:**
   - Всегда проверяйте наличие stale tasks
   - Убедитесь, что MySQL запущен
   - Проверьте свободное место на диске

2. **Во время работы:**
   - Периодически запускайте `monitor_workers.py`
   - Следите за временем выполнения задач
   - Обращайте внимание на рост числа failed задач

3. **После завершения:**
   - Проверьте итоговую статистику
   - Экспортируйте результаты
   - Очистите старые задачи (опционально)

4. **При проблемах:**
   - Сначала смотрите `monitor_workers.py`
   - Затем проверяйте логи
   - Используйте SQL для детального анализа

---

## 📚 Дополнительные ресурсы

- [ASYNC_PIPELINE_MIGRATION.md](doc/ASYNC_PIPELINE_MIGRATION.md) - Документация по async pipeline
- [БЫСТРЫЙ_СТАРТ_ASYNC.md](БЫСТРЫЙ_СТАРТ_ASYNC.md) - Быстрый старт
- [workers/db_task_queue.py](workers/db_task_queue.py) - Исходный код воркеров
