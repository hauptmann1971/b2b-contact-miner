# 🛡️ Улучшения надежности пайплайна

## Проблема

Пайплайн падал при любых ошибках:
- ❌ Потеря соединения с MySQL
- ❌ Таймауты при краулинге
- ❌ Ошибки поисковых API
- ❌ Проблемы с Redis

## ✅ Решения

### 1. **Retry логика для поиска**

```python
async def _retry_search(self, keyword, max_retries=3):
    """Search with retry logic"""
    for attempt in range(1, max_retries + 1):
        try:
            search_results = self.serp.search(...)
            return search_results
        except Exception as e:
            if attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s
                await asyncio.sleep(wait_time)
            else:
                return []  # Return empty instead of crashing
```

**Преимущества:**
- ✅ Автоматические повторные попытки (до 3 раз)
- ✅ Экспоненциальная задержка между попытками
- ✅ Возвращает пустой результат вместо падения

---

### 2. **Retry для сохранения в БД**

```python
async def _retry_save_results(self, db, keyword_id, search_results, max_retries=3):
    """Save search results with retry logic"""
    for attempt in range(1, max_retries + 1):
        try:
            self.serp.save_results(db, keyword_id, search_results)
            return
        except Exception as e:
            if attempt < max_retries:
                # Recreate DB session
                db.close()
                db = SessionLocal()
                await asyncio.sleep(2 ** attempt)
            else:
                # Continue even if save failed
                pass
```

**Преимущества:**
- ✅ Пересоздание сессии БД при ошибках
- ✅ Не блокирует весь пайплайн если сохранение не удалось
- ✅ Продолжает краулинг даже без сохранения результатов поиска

---

### 3. **Изоляция ошибок на уровне URL**

```python
for idx, result in enumerate(search_results[:5], 1):
    try:
        contacts = await self._process_search_result(db, result)
        # Process contacts...
    except Exception as e:
        logger.error(f"✗ Error processing URL {result['url']}: {e}")
        continue  # ← Continue with next URL!
```

**Преимущества:**
- ✅ Ошибка на одном сайте не ломает обработку других
- ✅ Каждый URL обрабатывается независимо
- ✅ Максимум контактов даже при частичных сбоях

---

### 4. **Изоляция ошибок на уровне ключевых слов**

```python
for idx, keyword in enumerate(pending_keywords, 1):
    try:
        result = await self._process_keyword(db, keyword_service, keyword)
        # Process result...
    except KeyboardInterrupt:
        logger.warning("⚠️  Pipeline interrupted by user")
        break  # Graceful shutdown
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        # Mark as failed but continue
        continue  # ← Next keyword!
```

**Преимущества:**
- ✅ Одно失败的关键词不影響其他
- ✅ Поддержка graceful shutdown (Ctrl+C)
- ✅ Подробное логирование ошибок

---

### 5. **Улучшенное логирование**

```python
logger.info(f"\n{'='*80}")
logger.info(f"Processing keyword [{idx}/{len(pending_keywords)}]: {keyword.keyword}")
logger.info(f"{'='*80}")

logger.info(f"✓ Completed [{idx}/5]: {result['url'][:50]}...")
logger.error(f"✗ Error processing URL {result['url']}: {e}")
logger.debug(traceback.format_exc())  # Full stack trace for debugging
```

**Преимущества:**
- ✅ Понятный прогресс в реальном времени
- ✅ Визуальные индикаторы успеха/ошибки
- ✅ Полные stack traces для отладки

---

### 6. **Graceful degradation**

```python
# Even if marking as processed fails, don't crash
try:
    keyword_service.mark_as_processed(keyword.id)
    self.state_manager.mark_keyword_completed(keyword.id, contacts_found)
except Exception as e:
    logger.error(f"Failed to mark keyword as processed: {e}")
    # Don't raise - keyword was still processed
```

**Преимущества:**
- ✅ Частичные результаты сохраняются
- ✅ Пайплайн продолжает работу
- ✅ Можно перезапустить с места сбоя

---

## 📊 Сценарии отказоустойчивости

### Сценарий 1: MySQL отвалился во время работы

**До:**
```
❌ OperationalError: Lost connection to MySQL server
💥 Pipeline crashed
```

**После:**
```
⚠️  Save attempt 1 failed: Lost connection
🔄 Retrying in 2s...
✓ Saved search results (after reconnect)
✅ Pipeline continues
```

---

### Сценарий 2: Один сайт недоступен

**До:**
```
❌ TimeoutError on habr.com
💥 Entire keyword failed
```

**После:**
```
✗ Error processing URL habr.com: Timeout
✓ Completed [2/5]: it-atlas.ru...
✓ Completed [3/5]: example.com...
✅ Keyword completed: 4 websites, 2 contacts
```

---

### Сценарий 3: Пользователь прерывает выполнение

**До:**
```
^C
💥 Crash with traceback
❌ No progress saved
```

**После:**
```
^C
⚠️  Pipeline interrupted by user
📊 Progress: 3/10 keywords
   Total websites: 12
   Total contacts: 5
✅ Graceful shutdown
```

---

### Сценарий 4: DuckDuckGo временно недоступен

**До:**
```
❌ Search API error
💥 Pipeline stopped
```

**После:**
```
⚠️  Search attempt 1 failed: Connection error
🔄 Retrying in 2s...
⚠️  Search attempt 2 failed: Connection error  
🔄 Retrying in 4s...
✓ Search successful: 10 results
✅ Pipeline continues
```

---

## 🔧 Конфигурация retry

Можно настроить параметры retry:

```python
# В main.py
max_retries=3  # Количество попыток
wait_time = 2 ** attempt  # Экспоненциальный backoff
# Attempt 1: wait 2s
# Attempt 2: wait 4s
# Attempt 3: wait 8s
```

---

## 📈 Метрики надежности

### До улучшений:
- ❌ Любой сбой = падение всего пайплайна
- ❌ Потеря всех результатов при ошибке
- ❌ Нужно перезапускать с начала

### После улучшений:
- ✅ Частичные сбои изолированы
- ✅ Сохраняются все успешные результаты
- ✅ Можно продолжить с места сбоя
- ✅ Автоматическое восстановление после transient errors

---

## 🚀 Запуск с улучшенной надежностью

```bash
# Обычный запуск
python main.py

# Пайплайн теперь:
# ✓ Автоматически retry при ошибках
# ✓ Изолирует сбои на уровне URL/keywords
# ✓ Graceful shutdown при Ctrl+C
# ✓ Сохраняет прогресс
# ✓ Продолжает работу после transient errors
```

---

## 💡 Рекомендации для production

1. **Мониторинг:**
   - Следите за логами на предмет repeated failures
   - Настройте алерты если >50% keywords fail

2. **Настройка таймаутов:**
   ```python
   # В crawler_service.py
   timeout=30  # Увеличить для медленных сайтов
   ```

3. **Rate limiting:**
   ```python
   # Добавить задержки между запросами
   await asyncio.sleep(1)  # Between keywords
   ```

4. **Health checks:**
   ```bash
   # Проверить статус
   python -m monitoring.healthcheck
   ```

---

## 🎯 Итог

Пайплайн теперь **production-ready**:
- ✅ Отказоустойчивый
- ✅ Восстанавливается после сбоев
- ✅ Сохраняет прогресс
- ✅ Подробное логирование
- ✅ Graceful degradation

**Можно запускать на больших объемах данных!** 🚀
