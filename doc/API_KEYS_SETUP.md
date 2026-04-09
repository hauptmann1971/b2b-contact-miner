# Инструкция по настройке API ключей

## 🎯 Настроено: DuckDuckGo + DeepSeek (ПОЛНОСТЬЮ БЕСПЛАТНО!)

---

## 1️⃣ DuckDuckGo (Поисковый провайдер) - БЕСПЛАТНО!

### Что это?
DuckDuckGo - поисковая система с фокусом на приватность. **Не требует API ключа!**

### Преимущества:
- ✅ **Полностью бесплатно** - без лимитов!
- ✅ Не требует регистрации
- ✅ Не нужен API ключ
- ✅ Хорошее покрытие для большинства запросов
- ✅ Privacy-focused

### Настройка:
Ничего делать не нужно! Просто убедитесь, что в `.env`:
```bash
SERP_API_PROVIDER=duckduckgo
```

### Ограничения:
- ⚠️ Может быть заблокирован в некоторых регионах (используйте VPN)
- ⚠️ Меньше результатов чем у Google
- ⚠️ Нет точной геолокации

### Альтернативы (если DuckDuckGo не работает):

| Провайдер | Free Tier | Требуется ключ | Ссылка |
|-----------|-----------|----------------|--------|
| **DuckDuckGo** | Безлимитно | ❌ Нет | Уже настроен! |
| **SerpAPI** | 100 searches/month | ✅ Да | https://serpapi.com |
| **Google Custom Search** | 100 queries/day | ✅ Да | https://developers.google.com/custom-search |
| **Brave Search API** | 2000 queries/month | ✅ Да | https://brave.com/search/api/ |

---

## 2️⃣ DeepSeek (LLM модель)

### Что это?
DeepSeek - китайская LLM модель, аналог GPT-3.5-turbo. Отличное качество, полностью бесплатна (пока в бете).

### Преимущества:
- ✅ **Бесплатно** (beta period)
- ✅ Качество ≈ GPT-3.5-turbo
- ✅ Отлично понимает русский и английский
- ✅ OpenAI-compatible API (минимум изменений в коде)
- ✅ Быстрый ответ

### Как получить ключ:

1. **Зарегистрируйтесь:** https://platform.deepseek.com
2. Войдите в аккаунт
3. Перейдите в "API Keys" section
4. Создайте новый API Key
5. Скопируйте ключ (выглядит как: `sk-xxxxx...`)
6. Вставьте в `.env`:
   ```bash
   DEEPSEEK_API_KEY=sk-ваш_ключ_здесь
   ```

### Документация API:
- Base URL: `https://api.deepseek.com/v1`
- Модель: `deepseek-chat`
- Совместима с OpenAI SDK

### Альтернативные китайские LLM:

| Модель | Free Tier | Качество | Ссылка |
|--------|-----------|----------|--------|
| **DeepSeek** | Бесплатно (beta) | ⭐⭐⭐⭐ | https://platform.deepseek.com |
| **Qwen (Alibaba)** | 1M tokens/month | ⭐⭐⭐⭐⭐ | https://help.aliyun.com/zh/model-studio |
| **Moonshot (Kimi)** | Generous limits | ⭐⭐⭐⭐ | https://platform.moonshot.cn |
| **Zhipu (ChatGLM)** | 1M tokens/month | ⭐⭐⭐⭐ | https://open.bigmodel.cn |

---

## 📝 Итоговая конфигурация .env

После получения ключа DeepSeek, ваш `.env` должен выглядеть так:

```bash
# Database
DATABASE_URL=mysql+pymysql://kalmyk3j_contact:*6oTrq%r%che@kalmyk3j.beget.tech:3306/kalmyk3j_contact

# Redis
REDIS_URL=redis://localhost:6379/0

# SERP API - DuckDuckGo (FREE!)
SERP_API_PROVIDER=duckduckgo

# LLM - DeepSeek (FREE during beta!)
DEEPSEEK_API_KEY=sk-abc123def456ghi789jkl012mno345pqr
USE_DEEPSEEK=true
USE_OPENAI=false
USE_LLM_EXTRACTION=true

# Crawler settings
MAX_PAGES_PER_DOMAIN=10
CONCURRENT_BROWSERS=5
HEADLESS_BROWSER=true
MAX_CONCURRENT_DOMAINS_PER_SITE=5

# Rate limiting
DELAY_BETWEEN_REQUESTS=1.0
MAX_RETRIES=3
```

**Важно:** Для DuckDuckGo API ключ НЕ НУЖЕН!

---

## ✅ Проверка настройки

### 1. Протестируйте DuckDuckGo:
```bash
.\venv\Scripts\python.exe test_duckduckgo.py
```

Должны увидеть результаты поиска без ошибок.

### 2. Протестируйте DeepSeek:
Создайте файл `test_deepseek.py`:

```python
from openai import OpenAI
from config.settings import settings

client = OpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "Say hello in Russian"}],
    max_tokens=50
)

print(response.choices[0].message.content)
```

Запустите:
```bash
.\venv\Scripts\python.exe test_deepseek.py
```

Должны увидеть приветствие на русском языке.

### 3. Запустите тесты:
```bash
.\venv\Scripts\python.exe -m pytest tests/ -v
```

---

## 💰 Стоимость использования

### DuckDuckGo:
- **Бесплатно!** Без лимитов
- Не требует регистрации
- Не требует API ключа

### DeepSeek:
- **Сейчас:** Бесплатно (beta period)
- **В будущем:** Ожидается ~$0.14/1M tokens (дешевле OpenAI в 10 раз!)
- **Для проекта:** При использовании только для obfuscated emails: ~$0.01-0.05/run

**Итого:** ПОЛНОСТЬЮ БЕСПЛАТНО! 🎉🎉🎉

---

## 🔧 Troubleshooting

### Ошибка: "Invalid API key"
- Проверьте, что ключ скопирован полностью
- Убедитесь, что нет лишних пробелов
- Проверьте статус аккаунта на сайте провайдера

### Ошибка: "Rate limit exceeded"
- SerpAPI: Подождите до следующего месяца или обновите план
- DeepSeek: Обычно лимиты высокие, проверьте dashboard

### Ошибка: "Connection timeout"
- Проверьте интернет соединение
- Попробуйте использовать VPN (для DeepSeek из некоторых регионов)
- Проверьте firewall/proxy настройки

### LLM не используется
- Убедитесь: `USE_DEEPSEEK=true` и `USE_LLM_EXTRACTION=true`
- Проверьте, что `DEEPSEEK_API_KEY` не пустой
- Смотрите логи на наличие ошибок подключения

---

## 🚀 Следующие шаги

1. ✅ DuckDuckGo уже настроен (не требует действий)
2. ✅ Получите API ключ DeepSeek (см. инструкции выше)
3. ✅ Обновите `.env` файл с DEEPSEEK_API_KEY
4. ✅ Протестируйте DuckDuckGo (`test_duckduckgo.py`)
5. ✅ Протестируйте DeepSeek (`test_deepseek.py`)
6. ✅ Запустите пайплайн:
   ```bash
   .\venv\Scripts\python.exe main.py
   ```

Готово! Ваш B2B Contact Miner настроен и работает ПОЛНОСТЬЮ БЕСПЛАТНО! 🎯🎉
