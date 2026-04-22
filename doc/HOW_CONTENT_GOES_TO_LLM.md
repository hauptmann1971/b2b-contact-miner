# Как контент страницы попадает в LLM Prompt

## 📊 Полный поток данных

```
1. Playwright crawls pages
         ↓
2. Extract text content from HTML
         ↓
3. Pass to extract_contacts() as List[Dict]
         ↓
4. Regex extracts contacts automatically
         ↓
5. IF obfuscated emails found → Add page content to LLM queue
         ↓
6. Combine all candidate pages into one string
         ↓
7. Insert into prompt template
         ↓
8. Send to LLM API
```

---

## 🔍 Детальное объяснение каждого шага

### Шаг 1-2: Crawling и извлечение текста

**Файл:** `services/crawler_service.py`

```python
async def crawl_contact_pages(self, base_url: str, contact_page_paths: List[str]) -> Dict:
    # Для каждой contact страницы:
    for path in contact_page_paths:
        full_url = urljoin(base_url, path)
        
        # Crawling через Playwright
        content = await self._crawl_page_with_rotation(page, full_url)
        
        if content:
            all_content.append({
                "url": full_url,
                "content": content,           # ← Чистый текст страницы
                "type": "contact_page",
                "priority": 10
            })
    
    return {
        "domain": domain,
        "content": all_content,  # ← Список словарей с контентом
        ...
    }
```

**Что такое `content`:**
- Это **чистый текст**, извлечённый из HTML через Playwright
- Без тегов, только видимый текст
- Пример: `"Contact us at info@example.com\nTelegram: @support"`

---

### Шаг 3: Передача в Extraction Service

**Файл:** `workers/db_task_queue.py`

```python
# Получаем данные от crawler
crawl_data = await crawler.crawl_contact_pages(url, contact_page_urls)

# crawl_data["content"] выглядит так:
[
    {
        "url": "https://example.com/contact",
        "content": "Наши контакты:\nEmail: info[at]example.com\nTelegram: @support",
        "type": "contact_page",
        "priority": 10
    },
    {
        "url": "https://example.com/about",
        "content": "About us...\nCEO: john (at) example (dot) com",
        "type": "about_page",
        "priority": 5
    }
]

# Передаём в extraction service
contacts, llm_data = extractor.extract_contacts(crawl_data["content"])
```

---

### Шаг 4: Regex извлечение (автоматически)

**Файл:** `services/extraction_service.py`

```python
def extract_contacts(self, content_list: List[Dict]) -> tuple:
    emails = set()
    telegram_links = set()
    linkedin_links = set()
    
    needs_llm_fallback = False
    llm_candidate_pages = []  # ← Сюда собираем страницы для LLM
    
    for item in content_list:
        content = item.get("content", "")  # ← Текст страницы
        url = item.get("url", "")
        page_type = item.get("type", "")
        
        # 1. Regex извлекает email
        found_emails = self.email_pattern.findall(content)
        
        # 2. Проверяем на обфускацию
        has_obfuscation = any(
            re.search(pattern, content, re.IGNORECASE) 
            for pattern in self.obfuscation_patterns
        )
        
        # 3. Если есть обфускация И мало email → добавляем в LLM queue
        if page_type == "contact_page" and has_obfuscation and len(emails) < 2:
            llm_candidate_pages.append(content[:3000])  # ← Обрезаем до 3000 символов
            needs_llm_fallback = True
```

---

### Шаг 5-6: Подготовка контента для LLM

```python
if needs_llm_fallback and settings.USE_LLM_EXTRACTION:
    # Объединяем все страницы-кандидаты в одну строку
    combined_content = "\n\n--- PAGE SEPARATOR ---\n\n".join(llm_candidate_pages)
    
    # combined_content теперь выглядит так:
    """
    Наши контакты:
    Email: info[at]example.com
    Telegram: @support
    
    --- PAGE SEPARATOR ---
    
    About us...
    CEO: john (at) example (dot) com
    """
```

---

### Шаг 7: Вставка в prompt template

**Файл:** `services/extraction_service.py`, строка 143-172

```python
prompt = f"""
Extract contact information from the following website content.

IMPORTANT RULES:
1. Return ONLY valid JSON, no additional text
2. Look for obfuscated emails like: name[at]domain.com, name (at) domain (dot) com
3. Find ALL Telegram contacts:
   - Links: t.me/username, telegram.me/username, join.chat/GROUP
   - Mentions: "Telegram: @username", "TG: @username", "@username"
4. Find ALL LinkedIn profiles:
   - Personal: linkedin.com/in/name
   - Company: linkedin.com/company/name
   - Any mention of LinkedIn with URL
5. Exclude generic emails: noreply@, support@, admin@, webmaster@
6. Include business emails even if they are info@ or sales@
7. Look for phone numbers in any format

Content to analyze:
{combined_content[:4000]}  # ← ЗДЕСЬ ВСТАВЛЯЕТСЯ КОНТЕНТ! (макс 4000 символов)

Return EXACTLY this JSON format (no extra text before or after):
{{
  "emails": ["email1@example.com", "email2@example.com"],
  "telegram": ["https://t.me/username", "@username", "https://join.chat/GROUP"],
  "linkedin": ["https://linkedin.com/in/name", "https://linkedin.com/company/name"]
}}

If no contacts found, return:
{{"emails": [], "telegram": [], "linkedin": []}}
"""
```

---

### Шаг 8: Отправка в LLM API

```python
# Для YandexGPT
response = requests.post(url, headers=headers, json={
    "modelUri": f"gpt://{folder_id}/yandexgpt/latest",
    "messages": [
        {"role": "user", "text": prompt}  # ← Весь prompt с контентом
    ]
})

# Для GigaChat
response = gc.chat(
    messages=[{"role": "user", "content": prompt}],
    temperature=0.1,
    max_tokens=300
)

# Для DeepSeek/OpenAI
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.1,
    max_tokens=300
)
```

---

## 📏 Ограничения размера

| Параметр | Значение | Где применяется |
|----------|----------|-----------------|
| **Одна страница для LLM** | 3000 символов | При добавлении в `llm_candidate_pages` |
| **Весь combined_content** | 4000 символов | При вставке в prompt (`combined_content[:4000]`) |
| **max_tokens ответа** | 300 токенов | Ограничение для LLM API |
| **temperature** | 0.1 | Низкая для детерминированных ответов |

---

## 💡 Важные моменты

### 1. **Какие страницы попадают в LLM?**
Только если выполнены ВСЕ условия:
- ✅ `page_type == "contact_page"` (страница контактов или about)
- ✅ `has_obfuscation == True` (найдены `[at]`, `(dot)` и т.п.)
- ✅ `len(emails) < 2` (обычный regex нашёл меньше 2 email)

### 2. **Сколько страниц может быть в одном запросе?**
- Теоретически: неограниченно
- Практически: ограничено 4000 символами итогового контента
- Обычно: 1-3 страницы

### 3. **Как разделяются страницы?**
```
Страница 1 контент

--- PAGE SEPARATOR ---

Страница 2 контент

--- PAGE SEPARATOR ---

Страница 3 контент
```

### 4. **Почему обрезается до 4000 символов?**
- Экономия токенов (меньше = дешевле)
- LLM не нужно читать весь сайт, только контактную информацию
- Большинство контактов находится в первых 2000-3000 символах

---

## 🎯 Пример полного цикла

### Входные данные (от crawler):
```python
content_list = [
    {
        "url": "https://example.com/contact",
        "content": """
            Contact Us
            
            For inquiries:
            Email: john.doe[at]company.com
            Phone: +1 (555) 123-4567
            
            Follow us:
            Telegram: https://t.me/example_company
            LinkedIn: linkedin.com/company/example
        """,
        "type": "contact_page"
    }
]
```

### После regex (шаг 4):
```python
emails = set()  # Пусто! [at] не распознан как email
has_obfuscation = True  # Найден паттерн [at]
needs_llm_fallback = True  # Нужно вызвать LLM
llm_candidate_pages = ["Contact Us\n\nFor inquiries:\nEmail: john.doe[at]company.com..."]
```

### Prompt для LLM (шаг 7):
```
Extract contact information from the following website content.

IMPORTANT RULES:
1. Return ONLY valid JSON, no additional text
2. Look for obfuscated emails like: name[at]domain.com...
...

Content to analyze:
Contact Us

For inquiries:
Email: john.doe[at]company.com
Phone: +1 (555) 123-4567

Follow us:
Telegram: https://t.me/example_company
LinkedIn: linkedin.com/company/example

Return EXACTLY this JSON format...
```

### Ответ от LLM:
```json
{
  "emails": ["john.doe@company.com"],
  "telegram": ["https://t.me/example_company"],
  "linkedin": ["https://linkedin.com/company/example"]
}
```

### Финальный результат:
```python
ContactInfo(
    emails=["john.doe@company.com"],
    telegram_links=["https://t.me/example_company"],
    linkedin_links=["https://linkedin.com/company/example"],
    phone_numbers=["+1 (555) 123-4567"]
)
```

---

## 🔧 Как изменить поведение

### Увеличить лимит символов:
```python
# services/extraction_service.py, строка 102
llm_candidate_pages.append(content[:5000])  # Было 3000

# Строка 161
{combined_content[:6000]}  # Было 4000
```

### Изменить условие вызова LLM:
```python
# Строка 101
if page_type == "contact_page" and has_obfuscation and len(emails) < 5:
# Было < 2, стало < 5 (LLM будет вызываться чаще)
```

### Всегда использовать LLM (для тестирования):
```python
# Строка 101-103
if page_type == "contact_page":  # Убрать проверку has_obfuscation
    llm_candidate_pages.append(content[:3000])
    needs_llm_fallback = True
```

---

## 📝 Резюме

**Контент страницы попадает в prompt через:**

1. **Playwright** извлекает чистый текст из HTML
2. **Crawler** возвращает список `[{url, content, type}]`
3. **Regex** анализирует контент и решает, нужен ли LLM
4. **ExtractionService** объединяет страницы-кандидаты
5. **f-string** вставляет контент в шаблон prompt
6. **LLM API** получает полный prompt с контентом и возвращает JSON

**Ключевые файлы:**
- `services/crawler_service.py` - crawling и извлечение текста
- `services/extraction_service.py` - regex + LLM extraction
- `workers/db_task_queue.py` - orchestration (вызывает crawler → extractor)
