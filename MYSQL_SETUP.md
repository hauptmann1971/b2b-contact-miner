# MySQL Migration Guide

## Быстрый старт с MySQL

### 1. Установите зависимости

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Установите и настройте MySQL

**Windows:**
- Скачайте installer с https://dev.mysql.com/downloads/installer/
- Выберите MySQL Server 8.0+
- Запомните root пароль

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
sudo systemctl enable mysql
```

**macOS:**
```bash
brew install mysql
brew services start mysql
```

### 3. Создайте базу данных

**Способ 1 (рекомендуется):**
```bash
mysql -u root -p < setup_mysql.sql
```

**Способ 2 (вручную):**
```bash
mysql -u root -p
```

```sql
CREATE DATABASE contact_miner CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'miner'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON contact_miner.* TO 'miner'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 4. Настройте .env файл

```bash
cp .env.example .env
```

Откройте `.env` и измените:

```bash
DATABASE_URL=mysql+pymysql://miner:your_secure_password@localhost:3306/contact_miner
```

Замените `your_secure_password` на пароль из шага 3.

### 5. Проверьте подключение

```bash
python test_mysql_connection.py
```

Должны увидеть:
```
✅ All tests passed! MySQL is ready to use.
```

### 6. Инициализируйте таблицы

Таблицы создаются автоматически при первом запуске `test_mysql_connection.py` или:

```bash
python -c "from models.database import init_db; init_db()"
```

### 7. Готово! Можете запускать пайплайн

```bash
python main.py
```

---

## Troubleshooting

### Ошибка: "Access denied for user 'miner'@'localhost'"

**Решение:**
1. Проверьте пароль в `.env` файле
2. Пересоздайте пользователя:
```sql
DROP USER IF EXISTS 'miner'@'localhost';
CREATE USER 'miner'@'localhost' IDENTIFIED BY 'new_password';
GRANT ALL PRIVILEGES ON contact_miner.* TO 'miner'@'localhost';
FLUSH PRIVILEGES;
```

### Ошибка: "Unknown database 'contact_miner'"

**Решение:**
Запустите `setup_mysql.sql`:
```bash
mysql -u root -p < setup_mysql.sql
```

### Ошибка: "Can't connect to MySQL server"

**Решение:**
1. Проверьте, что MySQL запущен:
   - Windows: `services.msc` → найдите MySQL
   - Linux: `sudo systemctl status mysql`
   - macOS: `brew services list`

2. Запустите MySQL:
   - Linux: `sudo systemctl start mysql`
   - macOS: `brew services start mysql`

### Ошибка: "ModuleNotFoundError: No module named 'pymysql'"

**Решение:**
```bash
pip install pymysql cryptography
```

### Ошибка: "Character set 'utf8mb4' is not supported"

**Решение:**
Обновите MySQL до версии 5.5.3 или выше (рекомендуется 8.0+):
```bash
mysql --version
```

---

## Отличия от PostgreSQL

| Характеристика | PostgreSQL | MySQL |
|----------------|------------|-------|
| Driver | psycopg2 | pymysql |
| URL формат | `postgresql://...` | `mysql+pymysql://...` |
| Auto-increment | SERIAL (авто) | autoincrement=True |
| Connection pool recycle | Не требуется | 3600 секунд |
| JSON support | Отлично | Хорошо (5.7+) |
| Performance (read) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Performance (write) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## Production Recommendations

### 1. Используйте connection pooling

В `models/database.py` уже настроено:
```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_recycle=3600,  # Важно для MySQL!
)
```

### 2. Настройте MySQL для production

В `/etc/mysql/my.cnf` или `my.ini`:

```ini
[mysqld]
max_connections = 200
innodb_buffer_pool_size = 2G  # 50-70% RAM
innodb_log_file_size = 512M
query_cache_size = 64M
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
```

### 3. Backup базы данных

```bash
# Backup
mysqldump -u miner -p contact_miner > backup_$(date +%Y%m%d).sql

# Restore
mysql -u miner -p contact_miner < backup_20260406.sql
```

### 4. Мониторинг

```sql
-- Проверка активных соединений
SHOW PROCESSLIST;

-- Статистика таблиц
SELECT table_name, table_rows, data_length, index_length
FROM information_schema.tables
WHERE table_schema = 'contact_miner';

-- Медленные запросы
SHOW VARIABLES LIKE 'slow_query_log%';
```

---

## Миграция с PostgreSQL на MySQL

Если у вас уже есть данные в PostgreSQL:

1. Экспорт из PostgreSQL:
```bash
pg_dump -U miner contact_miner > pg_backup.sql
```

2. Конвертация схемы (вручную или через инструменты)

3. Импорт в MySQL:
```bash
mysql -u miner -p contact_miner < mysql_schema.sql
```

Или используйте ETL инструменты like Apache Airflow, Talend.
