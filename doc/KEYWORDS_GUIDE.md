# 📝 Как осуществляется запрос ключевых слов

## Обзор процесса

Система B2B Contact Miner использует **многоязычный подход** к поиску контактов компаний. Вот полный процесс:

---

## 1️⃣ Добавление ключевого слова

### Через код (Python):

```python
from models.database import SessionLocal
from models.schemas import KeywordInput
from services.keyword_service import KeywordService

# Создать сессию БД
db = SessionLocal()
keyword_service = KeywordService(db)

# Добавить ключевое слово
keyword_data = KeywordInput(
    keyword="fintech startup",  # Ваше ключевое слово
    language="en",                # Язык ключа (ru, en, de, и т.д.)
    country="US"                  # Страна поиска (RU, US, DE, и т.д.)
)

keyword = keyword_service.add_keyword(keyword_data)
print(f"Added keyword ID: {keyword.id}")
```

### Автоматический перевод:

При добавлении ключевого слова система **автоматически генерирует переводы** на все целевые языки:

```python
# Пример: добавляем русское ключевое слово
keyword_data = KeywordInput(
    keyword="финтех стартап",
    language="ru",
    country="RU"
)

# Система автоматически создаст варианты:
# - ru: ["финтех стартап", "финтех компания", "финтех бизнес"]
# - en: ["fintech startup", "fintech company", "fintech business"]
# - de: ["fintech startup", "fintech unternehmen"]
# И сохранит их в базу данных
```

---

## 2️⃣ Генерация вариантов ключевых слов

Система автоматически создает **синонимы и связанные термины**:

### Встроенные синонимы:

```python
# Для русского языка:
"стартап" → ["компания", "бизнес", "предприятие"]
"финтех" → ["financial technology", "fintech"]

# Для английского:
"startup" → ["company", "business", "venture"]
"fintech" → ["financial technology"]
```

### Пример генерации:

```python
keyword_service = KeywordService(db)

# Исходное ключевое слово
translations = keyword_service.generate_translations(
    keyword="финтех стартап",
    source_lang="ru"
)

# Результат:
{
    "ru": ["финтех стартап", "финтех компания", "финтех бизнес"],
    "en": ["fintech startup", "fintech company", "fintech business"],
    "de": ["fintech startup", "fintech unternehmen"]
}
```

---

## 3️⃣ Поиск через SERP API

Для каждого ключевого слова выполняется поиск:

```python
from services.serp_service import SerpService

serp = SerpService()

# Выполнить поиск
results = serp.search(
    query="fintech startup Russia",  # Ключевое слово
    country="RU",                      # Страна
    language="ru",                     # Язык
    num_results=5                      # Количество результатов
)

# Результат: список URL сайтов
[
    {
        "url": "https://example-company.ru",
        "title": "Fintech Company - Financial Solutions",
        "snippet": "Leading fintech startup in Russia...",
        "position": 1
    },
    ...
]
```

### Поддерживаемые поисковые провайдеры:

1. **DuckDuckGo** (по умолчанию) ✅
   - Бесплатно, без API ключа
   - Хорошее покрытие
   - Настройка: `SERP_API_PROVIDER=duckduckgo`

2. **SerpAPI** (опционально)
   - 100 бесплатных поисков/месяц
   - Более точные результаты
   - Настройка: `SERP_API_PROVIDER=serpapi`

---

## 4️⃣ Полный пайплайн обработки

```
┌─────────────────────┐
│ 1. Добавить ключ    │  ← KeywordService.add_keyword()
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. Перевести на     │  ← TranslationService.translate()
│    все языки        │     + генерация синонимов
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. Сохранить в БД   │  ← MySQL таблица keywords
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 4. Получить         │  ← KeywordService.get_pending_keywords()
│    необработанные   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 5. Поиск в SERP     │  ← SerpService.search()
│    для каждого      │     DuckDuckGo / SerpAPI
│    варианта         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 6. Сохранить        │  ← MySQL таблица search_results
│    результаты       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 7. Обработать URL   │  ← CrawlerService.crawl_domain()
│    (краулинг)       │     Playwright браузер
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 8. Извлечь контакты │  ← ExtractionService.extract_contacts()
│    (email, TG, LI)  │     Regex + YandexGPT LLM
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 9. Верификация      │  ← MX records проверка email
│    email            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 10. Сохранить в БД  │  ← MySQL таблицы domain_contacts, contacts
└─────────────────────┘
```

---

## 5️⃣ Запуск полного пайплайна

### Основной скрипт:

```bash
# Запустить обработку всех pending keywords
python main.py
```

### Что происходит:

1. **Загружает** все необработанные ключевые слова из БД
2. **Для каждого ключа:**
   - Выполняет поиск через SERP API
   - Получает топ-5 URL
   - Краулит каждый сайт (до 10 страниц)
   - Извлекает email, Telegram, LinkedIn
   - Верифицирует email через MX records
   - Сохраняет результаты в БД
3. **Обновляет статус** ключа как "обработан"
4. **Показывает прогресс** в реальном времени

---

## 6️⃣ Мониторинг прогресса

### Проверка статуса ключевых слов:

```python
from models.database import SessionLocal
from services.keyword_service import KeywordService

db = SessionLocal()
keyword_service = KeywordService(db)

# Получить все ключевые слова
keywords = keyword_service.get_existing_keywords()

for kw in keywords:
    status = "✅ Processed" if kw["is_processed"] else "⏳ Pending"
    print(f"{kw['keyword']} ({kw['language']}) - {status}")

# Статистика по языкам
lang_summary = keyword_service.get_languages_summary()
print(f"\nKeywords per language: {lang_summary}")
```

### Прогресс текущего запуска:

```python
from utils.state_manager import StateManager

state_manager = StateManager()
stats = state_manager.get_run_stats()

print(f"Progress: {stats['progress_percent']}%")
print(f"Websites processed: {stats['websites_processed']}")
print(f"Contacts found: {stats['contacts_found']}")
```

---

## 7️⃣ Примеры использования

### Пример 1: Добавить одно ключевое слово

```python
from models.database import SessionLocal
from models.schemas import KeywordInput
from services.keyword_service import KeywordService

db = SessionLocal()
keyword_service = KeywordService(db)

# Добавить ключ
keyword = keyword_service.add_keyword(KeywordInput(
    keyword="AI startup Berlin",
    language="en",
    country="DE"
))

print(f"Keyword added with ID: {keyword.id}")
# Система автоматически создаст переводы на ru, de, fr и т.д.
```

### Пример 2: Добавить несколько ключей

```python
keywords = [
    ("fintech startup", "en", "US"),
    ("AI компания", "ru", "RU"),
    ("blockchain venture", "en", "GB"),
]

for keyword_text, lang, country in keywords:
    keyword_service.add_keyword(KeywordInput(
        keyword=keyword_text,
        language=lang,
        country=country
    ))

print(f"Added {len(keywords)} keywords")
```

### Пример 3: Запустить пайплайн

```bash
# Терминал 1: Запустить основной пайплайн
python main.py

# Терминал 2: Мониторить прогресс (опционально)
python -m monitoring.healthcheck
```

---

## 8️⃣ Конфигурация

### Файл `.env`:

```bash
# Поисковый провайдер
SERP_API_PROVIDER=duckduckgo  # или serpapi

# Языки для перевода
# (настраивается в config/settings.py)
LANGUAGES=["ru", "en", "de", "fr", "es"]

# Максимум результатов на ключ
MAX_SEARCH_RESULTS=5

# Максимум страниц на домен
MAX_PAGES_PER_DOMAIN=10
```

---

## 9️⃣ База данных

### Таблица `keywords`:

| Поле | Тип | Описание |
|------|-----|----------|
| id | INT | Уникальный ID |
| keyword | VARCHAR(500) | Текст ключевого слова |
| language | VARCHAR(10) | Язык (ru, en, de...) |
| country | VARCHAR(5) | Страна (RU, US, DE...) |
| is_processed | BOOLEAN | Обработано ли |
| last_crawled_at | DATETIME | Дата последнего краулинга |
| created_at | DATETIME | Дата создания |

### Таблица `search_results`:

| Поле | Тип | Описание |
|------|-----|----------|
| id | INT | Уникальный ID |
| keyword_id | INT | Ссылка на keywords.id |
| url | VARCHAR(2000) | URL найденного сайта |
| title | VARCHAR(1000) | Заголовок результата |
| snippet | TEXT | Описание результата |
| position | INT | Позиция в поиске (1-5) |

---

## 🔟 Troubleshooting

### Проблема: Ключевое слово не обрабатывается

**Решение:**
```python
# Проверить статус
keywords = keyword_service.get_existing_keywords()
pending = [k for k in keywords if not k["is_processed"]]
print(f"Pending keywords: {len(pending)}")

# Если ключ уже processed, сбросить статус
db.query(Keyword).filter(Keyword.id == KEYWORD_ID).update({
    "is_processed": False,
    "last_crawled_at": None
})
db.commit()
```

### Проблема: Нет результатов поиска

**Решение:**
1. Проверить поисковый провайдер: `SERP_API_PROVIDER=duckduckgo`
2. Попробовать другой язык/страну
3. Упростить ключевое слово
4. Проверить интернет-соединение

### Проблема: Слишком много переводов

**Решение:**
Отредактировать `config/settings.py`:
```python
LANGUAGES: List[str] = ["ru", "en"]  # Только нужные языки
```

---

## 📊 Статистика и отчеты

### Экспорт результатов:

```python
from services.export_service import ExportService

exporter = ExportService(db)

# Экспорт в CSV
csv_data = exporter.export_to_csv()
with open("contacts.csv", "wb") as f:
    f.write(csv_data)

# Экспорт в Excel
excel_data = exporter.export_to_excel()
with open("contacts.xlsx", "wb") as f:
    f.write(excel_data)

# Получить сводку
summary = exporter.get_export_summary()
print(f"Total domains: {summary['total_domains']}")
print(f"Total emails: {summary['total_emails']}")
print(f"Total Telegram: {summary['total_telegram']}")
```

---

## 🚀 Быстрый старт

```python
# 1. Добавить ключевые слова
from models.database import SessionLocal
from models.schemas import KeywordInput
from services.keyword_service import KeywordService

db = SessionLocal()
ks = KeywordService(db)

ks.add_keyword(KeywordInput(keyword="fintech startup", language="en", country="US"))
ks.add_keyword(KeywordInput(keyword="AI компания", language="ru", country="RU"))

# 2. Запустить пайплайн
# В терминале: python main.py

# 3. Дождаться завершения
# 4. Экспортировать результаты
from services.export_service import ExportService
exporter = ExportService(db)
csv_data = exporter.export_to_csv()
```

---

## 💡 Советы

1. **Используйте конкретные ключевые слова** для лучших результатов
   - ✅ "fintech startup Moscow"
   - ❌ "business"

2. **Добавляйте ключи на разных языках** для максимального охвата

3. **Мониторьте прогресс** через healthcheck API

4. **Настраивайте лимиты** в зависимости от ваших нужд:
   - `MAX_SEARCH_RESULTS` - сколько URL искать на ключ
   - `MAX_PAGES_PER_DOMAIN` - сколько страниц краулить на сайт

5. **Используйте Redis** для дедупликации доменов (ускоряет работу)

---

Готово! Теперь вы знаете, как работает система ключевых слов! 🎯
