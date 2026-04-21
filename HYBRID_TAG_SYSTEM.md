# Гибридная система определения предметной области (тегов)

## 📋 Обзор

Система автоматически определяет категорию/предметную область для каждого домена с контактами, используя **гибридный подход**:

1. **Keyword** - поисковый запрос как базовый тег
2. **LLM классификация** - AI определяет бизнес-категорию из контента сайта

---

## 🎯 Как это работает

### Шаг 1: Извлечение keyword

```python
# workers/db_task_queue.py
keyword_obj = db.query(Keyword).filter(Keyword.id == keyword_id).first()
if keyword_obj:
    tags.append(keyword_obj.keyword)  # Например: "fintech startup"
```

**Пример:**
- Keyword: `"fintech startup"`
- Tag: `["fintech startup"]`

---

### Шаг 2: LLM классификация категории

```python
# Combine content from first 3 pages
combined_content = "\n\n".join([
    item.get("content", "")[:1000] 
    for item in crawl_data["content"][:3]
])

# Call LLM to classify
llm_categories = extractor.classify_domain_category(
    combined_content, 
    keyword="fintech startup"
)
```

**LLM Prompt:**
```
Determine the business category/industry for this website.
Search keyword: fintech startup

Content:
[First 3000 chars of website content]

Return ONLY a JSON array with 1-3 category tags from this list:
fintech, blockchain, ai, machine-learning, software, saas, ecommerce, marketing, 
consulting, healthcare, education, real-estate, legal, accounting, hr, logistics, 
manufacturing, media, entertainment, gaming, cybersecurity, data-analytics, 
cloud-computing, iot, robotics, biotech, startup, enterprise, b2b, b2c

Example responses:
["fintech", "startup"]
["software", "saas", "enterprise"]
["ecommerce"]

If unclear, return: ["business"]
```

**Пример ответа LLM:**
```json
["fintech", "startup", "saas"]
```

---

### Шаг 3: Объединение тегов

```python
# Add LLM categories (avoid duplicates)
for category in llm_categories:
    if category.lower() not in [t.lower() for t in tags]:
        tags.append(category)

# Final tags: ["fintech startup", "fintech", "startup", "saas"]
```

---

## 📊 Примеры работы

### Пример 1: Fintech компания

**Keyword:** `"fintech startup Berlin"`

**Контент сайта:**
```
We are a leading fintech startup providing AI-powered payment solutions 
for e-commerce businesses. Our SaaS platform helps online retailers 
accept crypto payments...
```

**Результат:**
```python
tags = [
    "fintech startup Berlin",  # ← Keyword
    "fintech",                  # ← LLM
    "startup",                  # ← LLM
    "saas"                      # ← LLM
]
```

**В CSV экспорте:**
```
Предметная область: fintech, startup, saas
```
*(Keyword фильтруется как слишком специфичный)*

---

### Пример 2: AI компания

**Keyword:** `"AI company Moscow"`

**Контент сайта:**
```
Our company develops machine learning solutions for healthcare industry.
We provide computer vision and natural language processing services...
```

**Результат:**
```python
tags = [
    "AI company Moscow",  # ← Keyword
    "ai",                 # ← LLM
    "machine-learning",   # ← LLM
    "healthcare"          # ← LLM
]
```

**В CSV экспорте:**
```
Предметная область: ai, machine-learning, healthcare
```

---

### Пример 3: Неясная категория

**Keyword:** `"business consulting"`

**Контент сайта:**
```
Welcome to our corporate website. We offer various business services 
and solutions for enterprises worldwide...
```

**Результат:**
```python
tags = [
    "business consulting",  # ← Keyword
    "business"              # ← LLM (fallback)
]
```

**В CSV экспорте:**
```
Предметная область: business
```
*(Keyword фильтруется, остаётся только общий тег)*

---

## 🔧 Конфигурация

### Включение/выключение LLM классификации

```bash
# .env файл
USE_LLM_EXTRACTION=true   # Включить LLM классификацию (рекомендуется)
USE_LLM_EXTRACTION=false  # Только keyword (быстрее, бесплатно)
```

### Если LLM отключён:

```python
# Используется только keyword
tags = ["fintech startup Berlin"]
```

---

## 📏 Ограничения

| Параметр | Значение |
|----------|----------|
| **Максимум тегов** | 4 (1 keyword + 3 LLM категории) |
| **Контент для анализа** | Первые 3 страницы, по 1000 символов каждая |
| **Таймаут LLM** | 10 секунд |
| **Доступные категории** | 33 предопределённых тега |

---

## 🎨 Доступные категории

LLM выбирает из следующего списка:

```
fintech, blockchain, ai, machine-learning, software, saas, 
ecommerce, marketing, consulting, healthcare, education, 
real-estate, legal, accounting, hr, logistics, manufacturing, 
media, entertainment, gaming, cybersecurity, data-analytics, 
cloud-computing, iot, robotics, biotech, startup, enterprise, 
b2b, b2c
```

Если контент не подходит ни под одну категорию → `["business"]`

---

## 💡 Преимущества гибридного подхода

### ✅ Преимущества:

1. **Точность**
   - Keyword даёт контекст поиска
   - LLM анализирует реальный контент сайта

2. **Гибкость**
   - Работает даже если LLM недоступен (fallback на keyword)
   - Можно отключить LLM для экономии токенов

3. **Детализация**
   - Keyword: специфичный запрос пользователя
   - LLM: общие бизнес-категории

4. **Поиск и фильтрация**
   - Можно искать по keyword ("fintech startup")
   - Можно фильтровать по категории ("fintech", "ai")

---

## 🚀 Использование в экспорте

### CSV экспорт (flat format):

```python
# services/export_service.py
def _extract_subject_area(self, tags: list) -> str:
    """Extract subject area from tags"""
    if not tags or not isinstance(tags, list):
        return ''
    
    # Filter out generic tags
    generic_tags = {'b2b', 'company', 'business', 'website'}
    meaningful_tags = [tag for tag in tags if tag.lower() not in generic_tags]
    
    return ', '.join(meaningful_tags[:3])  # Top 3 tags
```

**Пример:**
```python
tags = ["fintech startup Berlin", "fintech", "startup", "saas"]
subject_area = "fintech, startup, saas"
```

---

## 🔍 Логирование

```
2026-04-21 14:30:15 | INFO | Added keyword as tag: fintech startup
2026-04-21 14:30:17 | INFO | Classified domain categories: ['fintech', 'startup', 'saas']
2026-04-21 14:30:17 | INFO | Final tags for example.com: ['fintech startup', 'fintech', 'startup', 'saas']
```

---

## 🛠️ Обработка ошибок

### Если LLM недоступен:

```python
try:
    llm_categories = extractor.classify_domain_category(...)
except Exception as e:
    logger.warning(f"LLM classification failed: {e}")
    tags = [keyword]  # Fallback to keyword only
```

### Если keyword не найден:

```python
keyword_obj = db.query(Keyword).filter(...).first()
if not keyword_obj:
    tags = []  # Пустые теги (редкий случай)
```

---

## 📝 Архитектура

```
Domain Contact Creation
         ↓
┌─────────────────────┐
│  Get Keyword Text   │ ← From database (Keyword table)
└──────────┬──────────┘
           ↓
    Add to tags[]
           ↓
┌─────────────────────┐
│  LLM Classification │ ← Analyze website content
│  (if enabled)       │    Return 1-3 categories
└──────────┬──────────┘
           ↓
    Merge & deduplicate
           ↓
┌─────────────────────┐
│  Save to Database   │ ← DomainContact.tags (JSON)
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  Export to CSV      │ ← Filter & format tags
└─────────────────────┘
```

---

## 🎯 Ключевые файлы

| Файл | Функция |
|------|---------|
| `services/extraction_service.py` | `classify_domain_category()` - LLM классификация |
| `workers/db_task_queue.py` | `_handle_extract_task()` - создание тегов |
| `main.py` | `process_domain()` - создание тегов (legacy mode) |
| `services/export_service.py` | `_extract_subject_area()` - форматирование для CSV |

---

## 💡 Рекомендации

1. **Для максимальной точности**: Оставьте `USE_LLM_EXTRACTION=true`
2. **Для экономии токенов**: Установите `USE_LLM_EXTRACTION=false` (только keyword)
3. **Для кастомных категорий**: Отредактируйте список в `classify_domain_category()`
4. **Для изменения количества тегов**: Измените `meaningful_tags[:3]` в export_service

---

## 🔮 Будущие улучшения

Возможные улучшения системы:

1. **Пользовательские категории**
   - Позволить пользователю задать свой список категорий
   
2. **Иерархические теги**
   - Подкатегории: `fintech > payments`, `ai > nlp`
   
3. **Обучение на feedback**
   - Пользователь корректирует теги → модель учится
   
4. **Мультиязычная классификация**
   - Поддержка категорий на разных языках
   
5. **Автоматическое расширение списка**
   - LLM предлагает новые категории → добавляются в список
