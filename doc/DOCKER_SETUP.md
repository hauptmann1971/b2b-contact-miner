# 🐳 Docker Setup для B2B Contact Miner

## Быстрый старт с Docker

Этот проект использует Docker для запуска Redis и MySQL.

---

## 📋 Предварительные требования

### 1. Установите Docker Desktop

**Windows:**
1. Скачайте с https://www.docker.com/products/docker-desktop/
2. Запустите установщик (требуются права администратора)
3. Перезагрузите компьютер
4. Запустите Docker Desktop

**Проверка установки:**
```powershell
docker --version
docker-compose --version
```

---

## 🚀 Запуск сервисов

### Вариант 1: Docker Compose (Рекомендуется!)

```powershell
# Запустить Redis и MySQL
docker-compose up -d

# Проверить статус
docker-compose ps

# Посмотреть логи
docker-compose logs -f

# Остановить
docker-compose down
```

### Вариант 2: Отдельные контейнеры

```powershell
# Запустить Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Запустить MySQL
docker run -d --name mysql ^
  -p 3306:3306 ^
  -e MYSQL_ROOT_PASSWORD=root_password ^
  -e MYSQL_DATABASE=contact_miner ^
  -e MYSQL_USER=miner ^
  -e MYSQL_PASSWORD=miner_password ^
  mysql:8.0

# Проверить
docker ps
```

---

## 🔧 Настройка проекта

### 1. Обновите `.env`:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# MySQL Configuration (если используете Docker MySQL)
DATABASE_URL=mysql+pymysql://miner:miner_password@localhost:3306/contact_miner
```

### 2. Запустите пайплайн:

```powershell
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

## 📊 Управление контейнерами

### Основные команды:

```powershell
# Запустить все сервисы
docker-compose up -d

# Остановить все сервисы
docker-compose down

# Перезапустить Redis
docker-compose restart redis

# Посмотреть логи Redis
docker-compose logs redis

# Посмотреть логи MySQL
docker-compose logs mysql

# Подключиться к Redis CLI
docker exec -it b2b-contact-miner-redis redis-cli

# Подключиться к MySQL
docker exec -it b2b-contact-miner-mysql mysql -u miner -p

# Удалить все данные (осторожно!)
docker-compose down -v
```

---

## 🔍 Мониторинг

### Redis Monitor:

```powershell
# Подключиться к Redis
docker exec -it b2b-contact-miner-redis redis-cli

# Внутри Redis CLI:
127.0.0.1:6379> ping
PONG

127.0.0.1:6379> info server
# Показывает информацию о сервере

127.0.0.1:6379> monitor
# Показывает все команды в реальном времени
```

### MySQL Monitor:

```powershell
# Подключиться к MySQL
docker exec -it b2b-contact-miner-mysql mysql -u miner -pminner_password contact_miner

# Внутри MySQL:
mysql> SHOW TABLES;
mysql> SELECT COUNT(*) FROM keywords;
mysql> SELECT COUNT(*) FROM contacts;
```

---

## 🛠️ Troubleshooting

### Проблема: Port already in use

```powershell
# Проверить, что использует порт 6379
netstat -ano | findstr :6379

# Остановить другой Redis или изменить порт в docker-compose.yml
```

### Проблема: Container won't start

```powershell
# Посмотреть логи
docker-compose logs redis
docker-compose logs mysql

# Пересоздать контейнер
docker-compose up -d --force-recreate redis
```

### Проблема: Connection refused

```powershell
# Проверить, запущены ли контейнеры
docker-compose ps

# Должны быть в статусе "Up"

# Перезапустить
docker-compose restart
```

---

## 💾 Persistence (Сохранение данных)

Docker Compose настроен с volumes для сохранения данных:

- `redis_data` - Данные Redis (persist между перезапусками)
- `mysql_data` - Данные MySQL (persist между перезапусками)

Чтобы удалить все данные:
```powershell
docker-compose down -v
```

---

## 🎯 Production Recommendations

Для production используйте:

1. **Отдельные хосты для Redis и MySQL**
2. **Backup стратегии**
3. **Monitoring (Prometheus + Grafana)**
4. **Security (пароли, SSL)**
5. **Resource limits в docker-compose.yml**

Пример с лимитами:
```yaml
services:
  redis:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

---

## 📚 Дополнительные ресурсы

- [Docker Documentation](https://docs.docker.com/)
- [Redis Documentation](https://redis.io/documentation)
- [MySQL Documentation](https://dev.mysql.com/doc/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
