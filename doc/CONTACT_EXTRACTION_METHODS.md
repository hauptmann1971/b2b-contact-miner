# Как извлекаются контакты в B2B Contact Miner

## 📋 Методы извлечения

### 1. **Regex (основной метод)** - применяется ко ВСЕМ страницам

#### Email
- Стандартные email: `user@domain.com`
- Mailto ссылки: `<a href="mailto:...">`
- Обфусцированные: `user[at]domain.com`, `user (at) domain (dot) com`

#### Telegram
```python
# Паттерны для поиска:
- t.me/username
- telegram.me/username
- "Telegram: @username" или "TG: @username"
- join.chat/GROUP_ID
- Любые ссылки с t.me в href атрибутах
```

#### LinkedIn
```python
# Паттерны для поиска:
- linkedin.com/in/name (личные профили)
- linkedin.com/company/name (компаний)
- Любые упоминания LinkedIn с URL
```

#### Телефоны
- Международные форматы: `+1 (555) 123-4567`
- Локальные форматы: `(555) 123-4567`, `555-123-4567`

---

### 2. **LLM Fallback (дополнительный метод)** - только для сложных случаев

**Когда используется:**
- ✅ Нашёл обфусцированные email (`[at]`, `(dot)`)
- ✅ И найдено меньше 2 email обычным regex
- ✅ `USE_LLM_EXTRACTION=true` в `.env`

**Что делает LLM:**
- Извлекает obfuscated emails
- Может найти дополнительные Telegram/LinkedIn, которые пропустил regex
- Возвращает структурированный JSON

**Поддерживаемые LLM (приоритет):**
1. YandexGPT
2. GigaChat
3. DeepSeek
4. OpenAI

---

## 🔧 Конфигурация

### Включение/выключение LLM
```bash
# .env файл
USE_LLM_EXTRACTION=true   # Включить LLM fallback
USE_LLM_EXTRACTION=false  # Только regex (быстрее, дешевле)
```

### Настройка LLM провайдера
```bash
# YandexGPT (по умолчанию)
USE_YANDEXGPT=true
YANDEX_IAM_TOKEN=your_token_here
YANDEX_FOLDER_ID=your_folder_id

# GigaChat
USE_GIGACHAT=true
GIGACHAT_CLIENT_ID=your_client_id
GIGACHAT_CLIENT_SECRET=your_secret

# DeepSeek
USE_DEEPSEEK=true
DEEPSEEK_API_KEY=your_api_key
```

---

## 📊 Сравнение методов

| Метод | Скорость | Точность | Стоимость | Когда использовать |
|-------|----------|----------|-----------|-------------------|
| **Regex** | ⚡ Быстро | 80-90% | Бесплатно | Основной метод для всех сайтов |
| **LLM** | 🐌 Медленно | 90-95% | $$$ | Только для obfuscated emails |

---

## 🎯 Примеры работы

### Пример 1: Обычная страница (только regex)
```html
Contact us: info@example.com
Telegram: https://t.me/example_bot
LinkedIn: https://linkedin.com/company/example
```
**Результат regex:** ✅ Все контакты найдены  
**LLM вызывается:** ❌ Нет (нет obfuscated emails)

---

### Пример 2: Obfuscated email (regex + LLM)
```html
Email: john[at]company[dot]com
Alternative: jane (at) company (dot) com
```
**Результат regex:** ⚠️ Найдены паттерны `[at]`, но не распознаны как email  
**LLM вызывается:** ✅ Да, извлечёт `john@company.com` и `jane@company.com`

---

### Пример 3: Сложные Telegram mentions
```html
Наш Telegram канал: @tech_news
Связаться: TG: @support_manager
Группа: join.chat/ABC123
```
**Результат regex:** ✅ Найдутся все три контакта (новые паттерны)  
**LLM вызывается:** ❌ Нет необходимости

---

## 🚀 Улучшения в последней версии

### Добавленные regex паттерны:
1. `telegram_at_pattern` - ищет `Telegram: @username`, `TG: @username`
2. `telegram_join_pattern` - ищет `join.chat/GROUP_ID`
3. `linkedin_text_pattern` - ищет явные упоминания LinkedIn с URL

### Улучшенный LLM prompt:
- Более детальные инструкции по поиску Telegram
- Явное указание искать `@username` mentions
- Поддержка `join.chat` ссылок
- Поиск company LinkedIn профилей

---

## 📝 Тестирование LLM

Для тестирования prompt с разными LLM используйте:

```bash
# Показать примеры контента из БД
python export_for_llm_test.py

# См. файл LLM_PROMPT_EXAMPLE.md для полного шаблона
```

---

## 💡 Рекомендации

1. **Для быстрого сканирования**: Используйте только regex (`USE_LLM_EXTRACTION=false`)
2. **Для максимальной точности**: Включите LLM fallback
3. **Для экономии токенов**: LLM вызывается автоматически только когда нужен
4. **Для улучшения результатов**: Добавьте больше примеров в prompt (few-shot learning)

---

## 🔍 Архитектура извлечения

```
Website Content
       ↓
┌──────────────┐
│   Playwright  │ ← Crawls pages (fast mode for contact pages)
└──────┬───────┘
       ↓
┌──────────────┐
│    Regex     │ ← Extracts emails, Telegram, LinkedIn, phones
│  Extraction  │    (applied to ALL pages automatically)
└──────┬───────┘
       ↓
Obfuscated? ──── YES ───→ ┌──────────────┐
Few emails?               │     LLM      │ ← Fallback for complex cases
                          │  Extraction  │    (selective, cost-optimized)
                          └──────┬───────┘
                                 ↓
                         Merge results
                                 ↓
┌──────────────┐
│  Validation  │ ← Email verification (MX records)
│   & Filter   │    Remove blocked domains
└──────┬───────┘
       ↓
┌──────────────┐
│   Database   │ ← Save to contacts_json + normalized table
└──────────────┘
```
