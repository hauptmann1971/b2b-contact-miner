# 🚀 Быстрый старт - Как работает проект

## Краткое описание

**B2B Contact Miner** автоматически ищет контакты компаний в интернете:

1. Берет ключевые слова из базы (например, "финтех стартап")
2. Ищет сайты через DuckDuckGo
3. Краулит найденные сайты
4. Извлекает email, Telegram, LinkedIn
5. Сохраняет результаты в MySQL

---

## 📁 Структура проекта (просто)

```
main.py                  ← Запуск пайплайна
│
├── services/            ← Основная логика
│   ├── keyword_service.py      → Управление ключами
│   ├── serp_service.py         → Поиск сайтов
│   ├── crawler_service.py      → Краулинг страниц
│   └── extraction_service.py   → Извлечение контактов
│
├── models/              ← База данных
│   └── database.py             → Таблицы MySQL
│
├── workers/             ← Параллельная обработка
│   └── task_worker.py          → 20 worker'ов
│
└── utils/               ← Утилиты
    ├── robots_checker.py       → Проверка robots.txt
    └── state_manager.py        → Прогресс пайплайна
```

---

## 🔄 Как работает (по шагам)

### Шаг 1: Добавление ключевых слов
```bash
python add_keywords.py
```
Добавляет ключи в таблицу `keywords`:
- "финтех стартап" (ru, RU)
- "fintech startup" (en, US)
- и т.д.

---

### Шаг 2: Запуск пайплайна
```bash
python main.py
```

**Что происходит внутри:**

```
1. main.py загружает настройки из .env
2. Подключается к MySQL
3. Запускает 20 worker'ов для параллельной работы
4. Берет первое ключевое слово: "финтех стартап"
```

---

### Шаг 3: Поиск сайтов (SERP Service)

```python
# В main.py вызывается:
search_results = serp.search(
    query="финтех стартап",
    country="RU",
    language="ru",
    num_results=10
)

# DuckDuckGo возвращает:
[
    {"url": "https://mkechinov.ru/fintech-startups.html", ...},
    {"url": "https://rb.ru/fintech/organizations/", ...},
    {"url": "https://vitvet.com/articles/finteh_startapy/", ...},
    ...
]
```

Сохраняется в таблицу `search_results`.

---

### Шаг 4: Краулинг каждого сайта (Crawler Service)

Для каждого из 5 сайтов:

```python
# 1. Проверка robots.txt
if not robots_checker.can_fetch(url):
    skip()  # Пропускаем если запрещено

# 2. Запуск браузера Playwright
browser = chromium.launch(headless=True)

# 3. Загрузка sitemap.xml (если есть)
sitemap_urls = load_sitemap(domain)

# 4. Приоритизация страниц
high_priority = ["/contact", "/contacts", "/about"]
medium_priority = ["/team", "/leadership"]
low_priority = [остальные страницы]

# 5. Краулинг по приоритету
for page in prioritized_pages[:10]:  # Максимум 10 страниц
    content = browser.goto(page, timeout=30000)
    
    # Если нашли контакты на /contact → ранняя остановка!
    if has_contacts(content):
        break  # Не краулим остальные страницы
```

**Пример из реального запуска:**
- **mkechinov.ru**: 1 страница за 42 сек → нашел email ✓
- **rb.ru**: 1 страница за 8 сек → нашел email ✓
- **wikipedia.org**: 10 страниц за 31 сек → нет email ✗
- **vitvet.com**: TIMEOUT на каждой странице (сайт блокирует ботов)

---

### Шаг 5: Извлечение контактов (Extraction Service)

```python
# Получаем HTML контент всех страниц
content_list = [
    {"url": ".../contact", "content": "<html>...", "type": "contact_page"},
    {"url": ".../about", "content": "<html>...", "type": "regular_page"}
]

# Применяем regex паттерны
emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
telegram = re.findall(r't\.me/([a-zA-Z0-9_]+)', content)
linkedin = re.findall(r'linkedin\.com/(in|company)/([a-zA-Z0-9_-]+)', content)

# Результат:
ContactInfo(
    emails=["info@mkechinov.ru"],
    telegram=[],
    linkedin=[]
)
```

#### Если email обфусцирован:
```python
# Обнаружена обфускация: info[at]company[dot]ru
if has_obfuscation(content):
    # Используем YandexGPT для парсинга
    llm_result = yandexgpt.extract_contacts(content)
    emails = llm_result.emails
```

#### Верификация email:
```python
# Проверяем MX записи домена
is_valid = verify_email_mx("info@mkechinov.ru")
# Возвращает True если MX записи существуют
```

---

### Шаг 6: Сохранение в базу данных

```sql
-- 1. DomainContact (информация о домене)
INSERT INTO domain_contacts (
    search_result_id, 
    domain, 
    confidence_score,
    extraction_method
) VALUES (1, 'mkechinov.ru', 40, 'regex');

-- 2. Contact (сам контакт)
INSERT INTO contacts (
    domain_contact_id,
    contact_type,
    value,
    is_verified
) VALUES (1, 'email', 'info@mkechinov.ru', true);
```

---

### Шаг 7: Переход к следующему сайту/ключу

После обработки всех 5 сайтов ключевого слова:
```python
# Отмечаем ключ как обработанный
keyword.is_processed = True
db.commit()

# Берем следующий ключ
next_keyword = get_next_pending_keyword()
```

---

## 🎯 Реальный пример результатов

После запуска с ключом "финтех стартап":

```
✅ Найдено контактов: 2

1. mkechinov.ru
   Email: info@mkechinov.ru
   Статус: MX верифицирован ✓
   Время: 42 секунды

2. rb.ru
   Email: team@rb.ru
   Статус: MX верифицирован ✓
   Время: 8 секунд

❌ Не найдено: wikipedia.org (нет бизнес-контактов)
⏸️ Пропущено: generation-startup.ru (robots.txt blocked)
⏳ Зависло: vitvet.com (таймауты на всех страницах)
```

---

## ⚙️ Настройки (файл .env)

```bash
# Сколько страниц краулить на одном сайте
MAX_PAGES_PER_DOMAIN=10

# Таймаут на одну страницу (секунды)
REQUEST_TIMEOUT=30

# Сколько сайтов обрабатывать на одно ключевое слово
# (в коде: search_results[:5])

# Какой поисковик использовать
SERP_API_PROVIDER=duckduckgo

# LLM для сложных случаев
USE_YANDEXGPT=true
YANDEX_IAM_TOKEN=...
YANDEX_FOLDER_ID=b1gqdgpgp7i6fctfrh44
```

---

## 🛡️ Защита от ошибок

### 1. Retry при сбоях
```python
# Если поиск не удался → повторить до 3 раз
@retry(stop=stop_after_attempt(3))
def search(...):
    ...
```

### 2. Изоляция ошибок
```python
try:
    crawl_website(url)
except Exception as e:
    logger.error(f"Failed: {e}")
    continue  # Переходим к следующему сайту
```

### 3. Graceful shutdown
```bash
# Нажатие Ctrl+C
^C
→ Сохраняем прогресс
→ Закрываем браузеры
→ Выходим корректно
```

---

## 📊 Мониторинг прогресса

В логах видно:
```
Processing keyword [1/10]: финтех стартап
  [1/5] Processing: https://mkechinov.ru/...
  ✓ Completed [1/5]: mkechinov.ru (1 email found)
  
  [2/5] Processing: https://rb.ru/...
  ✓ Completed [2/5]: rb.ru (1 email found)
  
📊 Progress: 2/5 websites processed
   Total contacts: 2
```

---

## 🔍 Просмотр результатов

```bash
# Посмотреть все найденные контакты
python view_results.py

# Или напрямую в БД
python check_db_raw.py
```

---

## 💡 Ключевые особенности

### ✅ Умный краулинг
- Сначала проверяет `/contact`, `/contacts`
- Если нашел → останавливается (экономия времени)
- Максимум 10 страниц на сайт

### ✅ Приоритизация
1. Высокий: contact, contacts, about, team
2. Средний: impressum, legal, privacy
3. Низкий: остальные страницы из sitemap

### ✅ Дедупликация
- Redis (если доступен) или in-memory
- Не краулит один домен дважды

### ✅ Верификация
- Проверка формата email
- MX records проверка
- Confidence score (уверенность в контакте)

---

## 🚨 Типичные проблемы

### 1. Сайт блокирует ботов
```
Error: Page.goto: Timeout 30000ms exceeded
```
**Решение:** Сайт пропускается, переходим к следующему

### 2. robots.txt запрещает
```
Blocked by robots.txt
```
**Решение:** Сайт пропускается автоматически

### 3. Нет контактов на сайте
```
Extracted: 0 emails, 0 Telegram, 0 LinkedIn
```
**Решение:** Переходим к следующему сайту

### 4. Потеря соединения с БД
```
Lost connection to MySQL server
```
**Решение:** Автоматическое переподключение (pool_pre_ping)

---

## 📈 Производительность

**Один ключевой слово (~5 сайтов):**
- Быстрые сайты: 2-3 минуты
- Медленные сайты: 5-10 минут
- С таймаутами: 15+ минут

**Параллелизм:**
- 20 worker'ов могут обрабатывать разные задачи одновременно
- Но сайты одного ключа обрабатываются последовательно

---

## 🎓 Итог

**B2B Contact Miner делает:**
1. 🔍 Ищет сайты по ключевым словам
2. 🕷️ Краулит найденные сайты умно (с приоритетами)
3. 📧 Извлекает контакты (email, Telegram, LinkedIn)
4. ✅ Верифицирует email через MX
5. 💾 Сохраняет всё в MySQL

**Всё полностью автоматизировано!** 🚀
