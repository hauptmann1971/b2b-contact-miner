# 🚀 Запуск приложения - Полное руководство

## Скрипты запуска

Проект включает скрипты для управления всеми компонентами системы:

- **`start_all.sh`** - Bash скрипт (Linux/Mac/Git Bash на Windows)
- **`start_all.bat`** - Batch скрипт (Windows CMD/PowerShell)

## Компоненты системы

При запуске активируются следующие сервисы:

1. **Redis** (опционально, через Docker) - дополнительный кэш (не обязателен для пайплайна)
2. **MySQL** (опционально, через Docker) - база данных
3. **FastAPI Monitoring Server** (порт 8000) - health check и мониторинг
4. **Flask Web Server** (порт 5000) - веб-интерфейс пользователя
5. **Task Scheduler** - планировщик ежедневных запусков пайплайна
6. **Main Pipeline** - основной процесс майнинга контактов (запускается вручную или по расписанию)

## Быстрый старт

### Windows (PowerShell/CMD)

```bash
# Запустить все сервисы
start_all.bat start

# Или просто двойной клик по файлу
start_all.bat
```

### Linux/Mac/Git Bash

```bash
# Сделать исполняемым
chmod +x start_all.sh

# Запустить все сервисы
./start_all.sh start

# Или просто
./start_all.sh
```

## Команды управления

### start - Запуск всех сервисов

```bash
# Bash
./start_all.sh start

# Windows
start_all.bat start
```

**Что происходит:**
1. Проверяет и запускает Docker контейнеры (MySQL и опционально Redis)
2. Запускает FastAPI сервер мониторинга на порту 8000
3. Запускает Flask веб-сервер на порту 5000
4. Запускает планировщик задач
5. Показывает статус всех сервисов

**Вывод:**
```
========================================
  B2B Contact Miner - Starting All Services
========================================

[1/6] Checking Docker services...
Starting MySQL (and optional Redis) with Docker...

[2/6] Starting FastAPI Monitoring Server (port 8000)...
monitoring started (PID: 12345, Log: logs/monitoring.log)

[3/6] Starting Flask Web Server (port 5000)...
web_server started (PID: 12346, Log: logs/web_server.log)

[4/6] Starting Task Scheduler...
scheduler started (PID: 12347, Log: logs/scheduler.log)

[5/6] Main Pipeline ready (run 'python main.py' manually or wait for scheduler)

[6/6] Checking service status...

  ✓ monitoring (PID: 12345, Port: 8000)
  ✓ web_server (PID: 12346, Port: 5000)
  ✓ scheduler (PID: 12347)

========================================
  All services started successfully!
========================================

Access points:
  • Flask Web UI:      http://localhost:5000
  • FastAPI Health:    http://localhost:8000/health
  • FastAPI Docs:      http://localhost:8000/docs

Logs directory: C:\...\logs
PIDs directory: C:\...\pids

To stop all services, run: ./start_all.sh stop
```

### stop - Остановка всех сервисов

```bash
# Bash
./start_all.sh stop

# Windows
start_all.bat stop
```

**Что происходит:**
1. Останавливает планировщик
2. Останавливает Flask веб-сервер
3. Останавливает FastAPI мониторинг
4. Опционально останавливает Docker контейнеры

### restart - Перезапуск всех сервисов

```bash
# Bash
./start_all.sh restart

# Windows
start_all.bat restart
```

Эквивалентно выполнению `stop` затем `start`.

### status - Проверка статуса сервисов

```bash
# Bash
./start_all.sh status

# Windows
start_all.bat status
```

**Пример вывода:**
```
Service Status:

  ✓ monitoring (PID: 12345, Port: 8000)
  ✓ web_server (PID: 12346, Port: 5000)
  ✓ scheduler (PID: 12347)

Docker Services:
NAME                STATUS              PORTS
mysql               Up 2 hours          0.0.0.0:3306->3306/tcp

Recent Logs:

monitoring:
  2026-04-10 16:30:00 INFO Health check API started
  2026-04-10 16:30:05 INFO GET /health 200 OK
  2026-04-10 16:30:10 INFO Database connection healthy

web_server:
  2026-04-10 16:30:00 INFO Serving Flask app 'web_server'
  2026-04-10 16:30:05 INFO GET / 200 OK
  2026-04-10 16:30:10 INFO GET /health-check 200 OK

scheduler:
  2026-04-10 16:30:00 INFO Scheduler started - pipeline will run daily at 02:00
```

### logs - Просмотр логов

```bash
# Все логи в реальном времени
./start_all.sh logs

# Логи конкретного сервиса
./start_all.sh logs monitoring
./start_all.sh logs web_server
./start_all.sh logs scheduler

# Windows
start_all.bat logs
start_all.bat logs monitoring
```

**Горячие клавиши:**
- `Ctrl+C` - выход из режима просмотра логов

### clean - Очистка временных файлов

```bash
# Bash
./start_all.sh clean

# Windows
start_all.bat clean
```

**Что удаляет:**
- PID файлы из папки `pids/`
- Логи старше 7 дней из папки `logs/`

## Доступные URL после запуска

### Веб-интерфейс (Flask - порт 5000)
- **Главная страница**: http://localhost:5000
- **Ключевые слова**: http://localhost:5000/keywords
- **Контакты**: http://localhost:5000/contacts
- **Health Check UI**: http://localhost:5000/health-check
- **API Documentation**: http://localhost:5000/api-docs

### Мониторинг (FastAPI - порт 8000)
- **Health Check**: http://localhost:8000/health
- **Liveness**: http://localhost:8000/health/live
- **Readiness**: http://localhost:8000/health/ready
- **API Stats**: http://localhost:8000/api/stats
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Структура директорий

```
b2b-contact-miner/
├── logs/                    # Логи сервисов (создается автоматически)
│   ├── monitoring.log      # Логи FastAPI сервера
│   ├── web_server.log      # Логи Flask сервера
│   └── scheduler.log       # Логи планировщика
├── pids/                    # PID файлы процессов (создается автоматически)
│   ├── monitoring.pid
│   ├── web_server.pid
│   └── scheduler.pid
├── start_all.sh            # Bash скрипт запуска
├── start_all.bat           # Windows batch скрипт
└── STARTUP_GUIDE.md        # Этот файл
```

## Ручной запуск компонентов

Если нужно запустить только определенные компоненты:

```bash
# Только Flask веб-сервер
py web_server.py

# Только FastAPI мониторинг
py monitoring/healthcheck.py

# Только планировщик
py scheduler.py

# Полный пайплайн майнинга
py main.py

# Пайплайн с конкретным ключевым словом
py getters/run_specific_keyword.py "финтех стартап"
```

## Автоматический запуск при старте системы

### Windows (Task Scheduler)

1. Откройте Task Scheduler
2. Создайте новую задачу
3. Действие: `C:\path\to\start_all.bat start`
4. Триггер: At startup

### Linux (systemd)

Создайте файл `/etc/systemd/system/b2b-contact-miner.service`:

```ini
[Unit]
Description=B2B Contact Miner
After=network.target docker.service

[Service]
Type=forking
User=your_username
WorkingDirectory=/path/to/b2b-contact-miner
ExecStart=/path/to/start_all.sh start
ExecStop=/path/to/start_all.sh stop
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Затем:
```bash
sudo systemctl enable b2b-contact-miner
sudo systemctl start b2b-contact-miner
```

### Mac (launchd)

Создайте plist файл в `~/Library/LaunchAgents/`

## Устранение неполадок

### Сервис не запускается

1. Проверьте логи:
   ```bash
   ./start_all.sh logs monitoring
   ```

2. Проверьте, свободен ли порт:
   ```bash
   # Windows
   netstat -ano | findstr :5000
   
   # Linux/Mac
   lsof -i :5000
   ```

3. Проверьте зависимости:
   ```bash
   py -m pip install -r requirements.txt
   ```

### Порт уже занят

Измените порт в соответствующем файле:
- Flask: `web_server.py` (последние строки)
- FastAPI: `monitoring/healthcheck.py` или `api_server.py`

### Docker не запускается

Установите Docker Desktop:
- Скачайте с https://www.docker.com/products/docker-desktop
- Запустите и дождитесь полной инициализации

Или используйте локальную установку MySQL без Docker (Redis не обязателен).

### PID файл существует, но процесс не работает

Выполните очистку:
```bash
./start_all.sh clean
```

## Мониторинг работы

### Через веб-интерфейс

Откройте http://localhost:5000/health-check для визуального мониторинга.

### Через API

```bash
# Проверка здоровья
curl http://localhost:8000/health

# Статистика системы
curl http://localhost:8000/api/stats

# Список ключевых слов
curl http://localhost:5000/api/keywords
```

### Через логи

```bash
# Следить за логами в реальном времени
tail -f logs/*.log

# Поиск ошибок
grep -i error logs/*.log

# Последние 50 строк
tail -n 50 logs/web_server.log
```

## Производительность

### Настройки воркеров

Параметры воркеров и очереди задаются через DB task queue (`workers/db_task_queue.py`) и настройки в `.env`/`config/settings.py`.

### Настройки пула БД

В `models/database.py`:

```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,        # Размер пула
    max_overflow=30,     # Максимальное превышение
    pool_recycle=3600,   # Переподключение каждый час
)
```

## Безопасность

### Production deployment

1. Отключите debug mode в `web_server.py`:
   ```python
   app.run(host='0.0.0.0', port=5000, debug=False)
   ```

2. Установите SECRET_KEY в `.env`:
   ```
   SECRET_KEY=your-secret-key-here
   ```

3. Используйте reverse proxy (nginx):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:5000;
       }
   }
   ```

4. Настройте HTTPS (Let's Encrypt)

5. Ограничьте доступ к API эндпоинтам

## Дополнительная информация

- [Документация Flask сервера](doc/WEB_SERVER_GUIDE.md)
- [Новые страницы интерфейса](NEW_PAGES_GUIDE.md)
- [Архитектура системы](doc/ARCHITECTURE.md)
- [Настройка Redis](doc/REDIS_SETUP.md)
- [Настройка Docker](doc/DOCKER_SETUP.md)
