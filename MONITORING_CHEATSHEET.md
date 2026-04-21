# 🚀 Шпаргалка по мониторингу воркеров

## Быстрые команды

### 1. Проверить состояние системы
```bash
python monitor_workers.py
```

**Что смотреть:**
- ✅ Нет ли зависших задач (stale tasks)
- 🔄 Какие задачи выполняются прямо сейчас
- ❌ Есть ли ошибки
- 📊 Общая статистика

---

### 2. Восстановить зависшие задачи
```bash
python recover_stale_tasks.py
```

**Когда использовать:**
- Если `monitor_workers.py` показывает stale tasks
- После краша pipeline
- Перед запуском нового keyword

---

### 3. Запустить pipeline
```bash
python main.py
```

**Автоматически при старте:**
- Проверяет и восстанавливает stale tasks
- Запускает 20 workers
- Обрабатывает все pending задачи

---

## Признаки проблем

### 🔴 Критические (требуют немедленного вмешательства)

| Признак | Диагностика | Решение |
|---------|-------------|---------|
| Pipeline не запускается | Ошибки в консоли | Проверить `.env`, MySQL |
| Все задачи в `pending` | Workers не стартовали | Перезапустить pipeline |
| Много `failed` (>20%) | Одинаковые ошибки | Посмотреть логи, исправить код |

### 🟡 Предупреждения (можно работать, но нужно проверить)

| Признак | Диагностика | Решение |
|---------|-------------|---------|
| Задача выполняется >5 мин | `monitor_workers.py` | Подождать или восстановить |
| Несколько stale tasks | `monitor_workers.py` | Запустить `recover_stale_tasks.py` |
| Timeout на сайтах | Логи с "Timeout" | Увеличить `CRAWL_TIMEOUT` |

### 🟢 Нормальное состояние

- `completed`: растёт
- `running`: 0-20 задач
- `failed`: <5% от общего числа
- Stale tasks: 0

---

## Типичные сценарии

### Сценарий 1: Запуск нового keyword

```bash
# 1. Добавить keyword через веб-интерфейс (http://localhost:5000)
# ИЛИ через SQL:
mysql -u b2b_user -p b2b_contact_miner -e "
  INSERT INTO keywords (keyword, language, country) 
  VALUES ('my new keyword', 'en', 'US');
"

# 2. Проверить состояние
python monitor_workers.py

# 3. Если есть stale tasks → восстановить
python recover_stale_tasks.py

# 4. Запустить pipeline
python main.py

# 5. Мониторить прогресс
python monitor_workers.py  # в отдельном терминале
```

---

### Сценарий 2: Pipeline завис

```bash
# 1. Остановить pipeline (Ctrl+C)

# 2. Проверить состояние
python monitor_workers.py

# 3. Восстановить зависшие задачи
python recover_stale_tasks.py

# 4. Перезапустить
python main.py
```

---

### Сценарий 3: Много ошибок

```bash
# 1. Посмотреть детали ошибок
python monitor_workers.py

# 2. Детальный анализ через SQL
mysql -u b2b_user -p b2b_contact_miner -e "
  SELECT task_type, LEFT(error_message, 100) as error, COUNT(*) as count
  FROM task_queue 
  WHERE status = 'failed' 
  GROUP BY task_type, LEFT(error_message, 100)
  ORDER BY count DESC;
"

# 3. Исправить причину
# ... редактирование кода ...

# 4. Очистить failed задачи (опционально)
mysql -u b2b_user -p b2b_contact_miner -e "
  DELETE FROM task_queue WHERE status = 'failed';
"

# 5. Перезапустить
python main.py
```

---

### Сценарий 4: Мониторинг во время работы

**Терминал 1:**
```bash
python main.py
```

**Терминал 2 (каждые 30 секунд):**
```bash
python monitor_workers.py
```

**Что смотреть:**
- Растёт ли `completed`
- Не растёт ли `failed`
- Нет ли stale tasks
- Время выполнения задач (< 5 минут)

---

## Настройки

### Изменить timeout для stale tasks

В `.env`:
```env
TASK_LOCK_TIMEOUT=300  # секунды (по умолчанию 5 минут)
```

**Рекомендации:**
- `120` - для быстрых проверок
- `300` - стандарт (5 минут)
- `600` - для медленных сайтов

После изменения перезапустить pipeline!

---

## Полезные SQL запросы

### Статистика по задачам
```sql
SELECT status, COUNT(*) as count, 
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM task_queue), 1) as percentage
FROM task_queue 
GROUP BY status;
```

### Самые долгие задачи
```sql
SELECT id, task_type, 
       TIMESTAMPDIFF(SECOND, locked_at, NOW()) as seconds_running
FROM task_queue
WHERE status = 'running'
ORDER BY seconds_running DESC
LIMIT 10;
```

### Ошибки по типам
```sql
SELECT task_type, LEFT(error_message, 80) as error, COUNT(*) as count
FROM task_queue 
WHERE status = 'failed'
GROUP BY task_type, LEFT(error_message, 80)
ORDER BY count DESC;
```

### Прогресс по keyword
```sql
SELECT k.keyword, 
       COUNT(DISTINCT sr.id) as search_results,
       COUNT(DISTINCT dc.id) as contacts_found
FROM keywords k
LEFT JOIN search_results sr ON sr.keyword_id = k.id
LEFT JOIN domain_contacts dc ON dc.search_result_id = sr.id
GROUP BY k.id, k.keyword
ORDER BY k.id DESC
LIMIT 10;
```

---

## Файлы для мониторинга

| Файл | Назначение |
|------|------------|
| `monitor_workers.py` | Полная диагностика системы |
| `recover_stale_tasks.py` | Восстановление зависших задач |
| `check_contacts.py` | Проверка контактов в БД |
| `export_flat.py` | Экспорт результатов в CSV |
| `MONITORING_GUIDE.md` | Подробная документация |

---

## Контакты поддержки

Если ничего не помогает:

1. Посмотрите логи: `logs/pipeline.log`
2. Проверьте настройки: `.env`
3. Убедитесь, что MySQL запущен
4. Перезапустите всё: `start_all.bat restart` (Windows) или `./start_all.sh restart` (Linux)

---

**💡 Совет:** Добавьте `monitor_workers.py` в cron/планировщик для автоматического мониторинга каждые 5 минут!
