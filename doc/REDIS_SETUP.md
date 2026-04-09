# 📦 Установка Redis на Windows

## Проблема

Redis официально не поддерживает Windows. Есть несколько вариантов:

---

## ✅ Вариант 1: Memurai (Рекомендуется!)

**Memurai** - это нативный порт Redis для Windows.

### Установка через Chocolatey:

```powershell
# Запустить PowerShell от имени Администратора!
choco install memurai-developer -y
```

### После установки:

```powershell
# Memurai автоматически запускается как служба
# Проверить статус:
Get-Service Memurai

# Запустить вручную:
Start-Service Memurai

# Остановить:
Stop-Service Memurai
```

### Подключение:

```python
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
r.ping()  # PONG
```

---

## ✅ Вариант 2: WSL2 (Windows Subsystem for Linux)

Если у вас установлен WSL2:

```bash
# В терминале WSL (Ubuntu)
sudo apt update
sudo apt install redis-server

# Запуск
sudo service redis-server start

# Проверка
redis-cli ping  # PONG
```

### Подключение из Windows:

```python
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
r.ping()  # Работает через WSL2 networking
```

---

## ✅ Вариант 3: Docker Desktop

Если установлен Docker:

```powershell
docker run -d --name redis -p 6379:6379 redis:latest
```

### Проверка:

```powershell
docker exec -it redis redis-cli ping  # PONG
```

---

## ⚠️ Вариант 4: Без Redis (текущий режим)

Проект работает **без Redis**, используя in-memory deduplication.

### Текущий статус:

```
✅ Пайплайн работает
✅ База данных MySQL работает
❌ Redis не доступен → fallback to in-memory
```

### Ограничения без Redis:

1. ❌ Нет дедупликации между перезапусками
2. ❌ Нет распределенного кэша
3. ❌ Health API показывает "unhealthy"
4. ❌ Task queue monitoring не работает между процессами

### Когда Redis НЕ нужен:

- ✅ Разработка и тестирование
- ✅ Однократные запуски пайплайна
- ✅ Небольшие объемы данных

### Когда Redis НУЖЕН:

- ✅ Production environment
- ✅ Множественные параллельные пайплайны
- ✅ Распределенная обработка
- ✅ Полноценный monitoring

---

## 🔧 Настройка после установки Redis

### 1. Обновите `.env`:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
```

### 2. Перезапустите пайплайн:

```bash
python main.py
```

### 3. Проверьте health monitoring:

```powershell
Invoke-WebRequest -Uri http://localhost:8000/health | ConvertFrom-Json
```

Должно показать:
```json
{
  "status": "healthy",
  "services": {
    "redis": {"status": "healthy"},
    "database": {"status": "healthy"},
    "task_queue": {"status": "healthy"}
  }
}
```

---

## 🚀 Быстрый старт с Memurai

```powershell
# 1. Установить (от Администратора)
choco install memurai-developer -y

# 2. Проверить службу
Get-Service Memurai

# 3. Запустить если не запущен
Start-Service Memurai

# 4. Обновить .env
# REDIS_URL=redis://localhost:6379/0

# 5. Запустить пайплайн
python main.py

# 6. Проверить health
curl http://localhost:8000/health
```

---

## 📊 Сравнение решений

| Решение | Сложность | Производительность | Persistence | Цена |
|---------|-----------|-------------------|-------------|------|
| **Memurai Developer** | ⭐ Легко | ⭐⭐⭐ Отлично | ✅ Да | Бесплатно (dev) |
| **WSL2 Redis** | ⭐⭐ Средне | ⭐⭐⭐ Отлично | ✅ Да | Бесплатно |
| **Docker** | ⭐⭐ Средне | ⭐⭐ Хорошо | ⚠️ Volatile | Бесплатно |
| **Без Redis** | ⭐ Легко | ⭐⭐ Нормально | ❌ Нет | Бесплатно |

---

## 💡 Рекомендация

**Для разработки:** Используйте текущий режим (без Redis) - всё работает!

**Для production:** Установите Memurai или Redis в WSL2 для полноценного мониторинга и дедупликации.
