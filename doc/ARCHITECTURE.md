# 🏗️ Архитектура B2B Contact Miner

## Обзор системы

**B2B Contact Miner** - это асинхронный пайплайн для автоматического поиска и извлечения контактной информации (email, Telegram, LinkedIn) с корпоративных сайтов.

---

## 📦 Структура модулей

```
b2b-contact-miner/
├── main.py                    # Точка входа, оркестрация пайплайна
├── config/
│   └── settings.py           # Конфигурация и настройки
├── models/
│   ├── database.py           # Модели БД (SQLAlchemy ORM)
│   └── schemas.py            # Pydantic схемы данных
├── services/
│   ├── keyword_service.py    # Управление ключевыми словами
│   ├── serp_service.py       # Поисковые API (DuckDuckGo, SerpAPI)
│   ├── crawler_service.py    # Краулинг сайтов (Playwright)
│   ├── extraction_service.py # Извлечение контактов (Regex + LLM)
│   ├── translation_service.py# Перевод ключевых слов
│   └── export_service.py     # Экспорт результатов
├── workers/
│   └── task_worker.py        # Асинхронная очередь задач
├── utils/
│   ├── robots_checker.py     # Проверка robots.txt
│   └── state_manager.py      # Управление состоянием пайплайна
└── monitoring/
    └── healthcheck.py        # Healthcheck API
```

---

## 🔄 Поток выполнения (Pipeline Flow)

### 1️⃣ **Инициализация** (`main.py:ContactMiningPipeline.__init__`)

```python
class ContactMiningPipeline:
    def __init__(self):
        init_db()                          # Инициализация БД
        self.serp = SerpService()          # Сервис поиска
        self.crawler = CrawlerService()    # Сервис краулинга
        self.extractor = ExtractionService() # Сервис извлечения
        self.state_manager = StateManager() # Менеджер состояния
        self.robots_checker = RobotsChecker() # Проверка robots.txt
```

**Что происходит:**
- Подключение к MySQL базе данных
- Создание экземпляров всех сервисов
- Настройка логирования

---

### 2️⃣ **Запуск пайплайна** (`main.py:run_pipeline`)

```python
async def run_pipeline(self):
    await self.initialize()  # Инициализация Redis и worker'ов
    
    db = SessionLocal()
    pending_keywords = keyword_service.get_pending_keywords()
    
    for keyword in pending_keywords:
        result = await self._process_keyword(db, keyword)
```

**Шаги:**
1. Подключение к Redis (опционально, для дедупликации)
2. Запуск 20 асинхронных worker'ов
3. Получение списка необработанных ключевых слов
4. Последовательная обработка каждого ключевого слова

---

### 3️⃣ **Обработка ключевого слова** (`main.py:_process_keyword`)

```python
async def _process_keyword(self, db, keyword):
    # Шаг 1: Поиск через SERP API
    search_results = await self._retry_search(keyword)
    
    # Шаг 2: Сохранение результатов поиска в БД
    await self._retry_save_results(db, keyword.id, search_results)
    
    # Шаг 3: Обработка каждого найденного сайта (до 5)
    for result in search_results[:5]:
        contacts = await self._process_search_result(result)
```

---

## 🔍 Детальное описание модулей

### **A. Keyword Service** (`services/keyword_service.py`)

**Ответственность:** Управление ключевыми словами для поиска

**Основные методы:**
```python
add_keyword(keyword_data: KeywordInput)  # Добавить ключевое слово
get_pending_keywords()                    # Получить необработанные ключи
mark_as_processed(keyword_id)            # Отметить как обработанное
translate_and_expand(keyword)            # Перевести и расширить синонимами
```

**Пример использования:**
```python
ks = KeywordService(db)
ks.add_keyword(KeywordInput(
    keyword="финтех стартап",
    language="ru",
    country="RU"
))
```

---

### **B. SERP Service** (`services/serp_service.py`)

**Ответственность:** Поиск сайтов через поисковые системы

**Поддерживаемые провайдеры:**
- ✅ **DuckDuckGo** (бесплатно, без API ключа) - используется по умолчанию
- 🔑 **SerpAPI** (требует API ключ)
- 🔑 **BrightData** (требует API ключ)
- 🔑 **ScraperAPI** (требует API ключ)

**Как работает:**
```python
def search(query, country="RU", language="ru", num_results=10):
    # 1. Определяет регион поиска (ru-ru, us-en, de-de...)
    # 2. Выполняет HTTP запрос к поисковому API
    # 3. Парсит результаты (URL, title, snippet)
    # 4. Возвращает список словарей
    return [{"url": "...", "title": "...", "snippet": "..."}]
```

**Retry логика:** Автоматические повторные попытки при ошибках (до 3 раз)

---

### **C. Crawler Service** (`services/crawler_service.py`)

**Ответственность:** Краулинг веб-сайтов с помощью Playwright

**Ключевые особенности:**

1. **Приоритизация страниц:**
   ```python
   # Высокий приоритет (краулятся первыми):
   /contact, /contacts, /about, /team, /leadership
   
   # Средний приоритет:
   /impressum, /legal, /privacy
   
   # Низкий приоритет:
   Остальные страницы из sitemap
   ```

2. **Умная остановка:**
   - Если контакты найдены на странице с высоким приоритетом → остановка
   - Максимум 10 страниц на домен (настраивается в `.env`)
   - Таймаут 30 секунд на страницу

3. **Rate Limiting:**
   - Semaphore для ограничения одновременных запросов к одному домену
   - Максимум 5 параллельных запросов на домен

**Как работает:**
```python
async def crawl_domain(base_url):
    # 1. Проверяет кэш (Redis или in-memory)
    # 2. Запускает браузер Chromium (headless)
    # 3. Загружает sitemap.xml (если есть)
    # 4. Строит приоритизированную очередь URL
    # 5. Краулит страницы по приоритету
    # 6. Извлекает HTML контент каждой страницы
    # 7. Возвращает список {url, content, type}
```

---

### **D. Extraction Service** (`services/extraction_service.py`)

**Ответственность:** Извлечение контактной информации из HTML

**Методы извлечения:**

#### 1. **Regex-based (быстрый, бесплатный)**
```python
# Email паттерны
[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
href="mailto:(.*?)"

# Telegram
t.me/username
telegram.me/username

# LinkedIn
linkedin.com/in/username
linkedin.com/company/name

# Телефоны
+7 (999) 123-45-67
```

#### 2. **LLM Fallback (для обфусцированных email)**
```python
# Срабатывает если:
# - Страница типа "contact_page"
# - Есть признаки обфускации ([at], [dot], {@})
# - Найдено меньше 2 email

# Использует YandexGPT для парсинга сложных случаев
```

#### 3. **Email верификация (MX records)**
```python
def verify_email(email):
    # 1. Проверяет формат (email-validator)
    # 2. Ищет MX записи домена
    # 3. Возвращает True/False
```

**Результат:**
```python
ContactInfo(
    emails=["info@company.ru"],
    telegram=["https://t.me/company"],
    linkedin=["https://linkedin.com/company/name"],
    phones=["+79991234567"]
)
```

---

### **E. Task Worker** (`workers/task_worker.py`)

**Ответственность:** Асинхронная очередь задач (замена Celery)

**Архитектура:**
```
┌─────────────┐
│   Queue     │ ← asyncio.Queue(maxsize=1000)
└──────┬──────┘
       │
  ┌────┼────┐
  │    │    │
  ▼    ▼    ▼
W1   W2   ... W20  ← 20 worker'ов обрабатывают задачи параллельно
```

**Как работает:**
```python
# Добавление задачи
await task_queue.add_task(crawl_function, url="...")

# Worker автоматически:
# 1. Берет задачу из очереди
# 2. Выполняет async функцию
# 3. Обрабатывает ошибки
# 4. Переходит к следующей задаче
```

---

### **F. Database Models** (`models/database.py`)

**Схема базы данных:**

```
┌──────────────┐       ┌──────────────────┐
│   keywords   │1────*│ search_results   │
└──────────────┘       └────────┬─────────┘
                                │
                           1────┴────*
                     ┌──────────────────┐
                     │ domain_contacts  │
                     └────────┬─────────┘
                              │
                         1────┴────*
                     ┌──────────────────┐
                     │    contacts      │
                     └──────────────────┘
```

**Таблицы:**

1. **keywords** - Ключевые слова для поиска
   - `id`, `keyword`, `language`, `country`, `is_processed`

2. **search_results** - Результаты поисковой выдачи
   - `id`, `keyword_id`, `url`, `title`, `snippet`, `position`

3. **domain_contacts** - Информация о домене
   - `id`, `search_result_id`, `domain`, `confidence_score`, `extraction_method`

4. **contacts** - Нормализованные контакты
   - `id`, `domain_contact_id`, `contact_type` (email/telegram/linkedin), `value`, `is_verified`

---

### **G. Utils**

#### **Robots Checker** (`utils/robots_checker.py`)
```python
# Проверяет robots.txt перед краулингом
if not robots_checker.can_fetch(url):
    logger.info("Skipping (robots.txt blocked)")
    continue
```

#### **State Manager** (`utils/state_manager.py`)
```python
# Отслеживает прогресс пайплайна
state_manager.update_progress(
    current_keyword=idx,
    total_keywords=len(keywords),
    websites_processed=count
)
```

---

## 🚀 Полный цикл работы (на примере)

### Пример: Поиск по ключу "финтех стартап"

```
1. KEYWORD SERVICE
   ↓ Получает ключевое слово из БД
   keyword = "финтех стартап" (ru, RU)

2. SERP SERVICE
   ↓ Ищет через DuckDuckGo с регионом ru-ru
   Найденные сайты:
   - mkechinov.ru/fintech-startups.html
   - rb.ru/fintech/organizations/
   - vitvet.com/articles/finteh_startapy/

3. Для каждого сайта (до 5):
   
   a) ROBOTS CHECKER
      ↓ Проверяет robots.txt
      ✓ Разрешено / ✗ Заблокировано
   
   b) CRAWLER SERVICE
      ↓ Запускает Playwright
      ↓ Загружает sitemap (если есть)
      ↓ Приоритизирует страницы:
         1. /contact (высокий приоритет)
         2. /contacts (высокий приоритет)
         3. Остальные (низкий приоритет)
      ↓ Краулит до 10 страниц или пока не найдет контакты
      
      Пример mkechinov.ru:
      - Попытка /contact → TIMEOUT 30с
      - Успех /contacts → Нашел email!
      - Ранняя остановка (умная оптимизация)
   
   c) EXTRACTION SERVICE
      ↓ Применяет regex паттерны
      ↓ Извлекает: info@mkechinov.ru
      ↓ Верифицирует MX записи ✓
      ↓ Если обфускация → использует YandexGPT
   
   d) DATABASE
      ↓ Сохраняет DomainContact
      ↓ Сохраняет Contact (email)
      ↓ Обновляет статус

4. STATE MANAGER
   ↓ Обновляет прогресс
   "Обработано 1/5 сайтов, найдено 1 контакт"

5. Повторяется для следующего сайта...
```

---

## ⚙️ Конфигурация (`.env`)

```bash
# База данных
DATABASE_URL=mysql+pymysql://user:pass@host:3306/dbname

# Поиск
SERP_API_PROVIDER=duckduckgo

# LLM (для сложных случаев)
YANDEX_IAM_TOKEN=...
YANDEX_FOLDER_ID=b1gqdgpgp7i6fctfrh44
USE_YANDEXGPT=true

# Краулер
MAX_PAGES_PER_DOMAIN=10        # Макс страниц на сайт
REQUEST_TIMEOUT=30             # Таймаут на страницу (сек)
CONCURRENT_BROWSERS=5          # Параллельных браузеров
```

---

## 🛡️ Механизмы надежности

### 1. **Retry Logic** (tenacity)
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential())
def search(...):
    # Автоматические повторные попытки при ошибках
```

### 2. **Error Isolation**
```python
try:
    process_website(url)
except Exception as e:
    logger.error(f"Failed: {e}")
    continue  # Переходим к следующему сайту
```

### 3. **Graceful Shutdown**
```python
try:
    await run_pipeline()
except KeyboardInterrupt:
    logger.info("Saving progress...")
    save_state()  # Сохраняем прогресс при Ctrl+C
```

### 4. **Connection Pool Management**
```python
engine = create_engine(
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,  # Проверка соединений
    connect_timeout=60
)
```

---

## 📊 Мониторинг

### Healthcheck API (`monitoring/healthcheck.py`)
```bash
curl http://localhost:8000/health
```

Возвращает:
- Статус Redis
- Количество worker'ов
- Размер очереди задач
- Статистику пайплайна

---

## 🎯 Ключевые преимущества архитектуры

1. **Асинхронность** - высокая производительность через asyncio
2. **Модульность** - каждый сервис независим и тестируем
3. **Масштабируемость** - легко добавить новые источники поиска
4. **Надежность** - retry, error isolation, graceful shutdown
5. **Гибкость** - поддержка разных LLM и поисковых провайдеров
6. **Эффективность** - умная приоритизация и ранняя остановка

---

## 🔧 Расширение системы

### Добавить новый поисковый провайдер:
1. Добавить метод `_newprovider_search()` в `SerpService`
2. Обновить `search()` метод с новым provider
3. Добавить API ключ в `.env` и `settings.py`

### Добавить новый тип контакта:
1. Добавить в `ContactType` enum
2. Добавить regex паттерн в `ExtractionService`
3. Обновить схему БД (миграция)

### Изменить стратегию краулинга:
1. Настроить `MAX_PAGES_PER_DOMAIN` в `.env`
2. Изменить приоритеты в `_build_prioritized_queue()`
3. Настроить таймауты в `REQUEST_TIMEOUT`
