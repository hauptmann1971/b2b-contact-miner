# Пример запроса к LLM для извлечения контактов

## System Prompt (если поддерживается):
```
You are a contact information extraction specialist. Your task is to find and extract contact details from website content.
```

## User Prompt:
```
Extract contact information from the following website content.

IMPORTANT RULES:
1. Return ONLY valid JSON, no additional text
2. Look for obfuscated emails like: name[at]domain.com, name (at) domain (dot) com
3. Find Telegram links: t.me/username, telegram.me/username, @username
4. Find LinkedIn profiles: linkedin.com/in/name, linkedin.com/company/name
5. Exclude generic emails: noreply@, support@, admin@, webmaster@
6. Include business emails even if they are info@ or sales@

Content to analyze:
[ВСТАВЬТЕ СЮДА КОНТЕНТ СТРАНИЦЫ - до 4000 символов]

Return EXACTLY this JSON format (no extra text before or after):
{
  "emails": ["email1@example.com", "email2@example.com"],
  "telegram": ["https://t.me/username", "@username"],
  "linkedin": ["https://linkedin.com/in/name"]
}

If no contacts found, return:
{"emails": [], "telegram": [], "linkedin": []}
```

## Параметры генерации:
- temperature: 0.1 (низкая температура для детерминированных результатов)
- max_tokens: 300 (достаточно для JSON ответа)

## Примеры контента для тестирования:

### Пример 1: Страница с обфусцированными email
```
Contact Us

For business inquiries, please reach out to us:
Email: john.doe[at]company.com
Alternative: jane.smith (at) company (dot) com

Follow us on social media:
Telegram: https://t.me/company_official
LinkedIn: https://www.linkedin.com/company/example-company

Phone: +1 (555) 123-4567
```

Ожидаемый ответ:
```json
{
  "emails": ["john.doe@company.com", "jane.smith@company.com"],
  "telegram": ["https://t.me/company_official"],
  "linkedin": ["https://www.linkedin.com/company/example-company"]
}
```

### Пример 2: Страница без контактов
```
About Our Company

We are a leading technology company founded in 2020.
Our mission is to innovate and deliver excellence.

Copyright 2024 Example Corp.
```

Ожидаемый ответ:
```json
{"emails": [], "telegram": [], "linkedin": []}
```

### Пример 3: Смешанный контент
```
Welcome to Tech Startup

Team:
- CEO: alex@techstartup.io
- CTO: maria [at] techstartup [dot] io

Connect with us:
- Telegram channel: @techstartup_news
- Personal Telegram: https://t.me/alex_ceo
- Company LinkedIn: linkedin.com/company/tech-startup
- Founder LinkedIn: https://linkedin.com/in/alex-founder

General inquiries: info@techstartup.io
Support: support@techstartup.io (исключить!)
```

Ожидаемый ответ:
```json
{
  "emails": ["alex@techstartup.io", "maria@techstartup.io", "info@techstartup.io"],
  "telegram": ["@techstartup_news", "https://t.me/alex_ceo"],
  "linkedin": ["linkedin.com/company/tech-startup", "https://linkedin.com/in/alex-founder"]
}
```

## Советы по тестированию:

1. **Для ChatGPT**: Используйте GPT-4 или GPT-3.5-turbo с temperature=0.1
2. **Для DeepSeek**: Используйте модель deepseek-chat через API или веб-интерфейс
3. **Для YandexGPT**: Используйте yandexgpt/latest через их API
4. **Проверяйте**: Ответ должен быть ТОЛЬКО JSON, без дополнительного текста

## Частые проблемы:

❌ **Плохой ответ** (с текстом вокруг JSON):
```
Here's the extracted information:

{
  "emails": ["test@example.com"]
}

Hope this helps!
```

✅ **Хороший ответ** (только JSON):
```json
{
  "emails": ["test@example.com"],
  "telegram": [],
  "linkedin": []
}
```

## Как улучшить результаты:

1. Добавьте больше примеров в prompt (few-shot learning)
2. Укажите явно, что нужно искать @username в тексте
3. Добавьте правила для разных форматов LinkedIn URL
4. Уточните, какие email считать бизнес-контактами
