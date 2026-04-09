# Инструкция по настройке GigaChat (Sber)

## 🎯 GigaChat от Сбера - Бесплатно для разработчиков!

---

## Что такое GigaChat?

GigaChat - это большая языковая модель от Сбера, отлично понимающая русский язык.

### Преимущества:
- ✅ **Бесплатно** для разработчиков
- ✅ Отличное понимание русского языка
- ✅ Хорошее качество генерации
- ✅ Активная поддержка и документация
- ✅ Российская разработка (нет проблем с доступом)

---

## Как получить credentials:

### Шаг 1: Регистрация в Sber Developers

1. **Перейдите на:** https://developers.sber.ru/
2. Нажмите **"Войти"** или **"Зарегистрироваться"**
3. Зарегистрируйтесь через:
   - Сбер ID (если есть)
   - Email
   - Социальные сети

### Шаг 2: Создание проекта GigaChat

1. После входа перейдите в раздел **"GigaChat"**
   - Или напрямую: https://developers.sber.ru/gigachat
   
2. Нажмите **"Подключить API"** или **"Создать проект"**

3. Заполните информацию о проекте:
   - Название проекта (например: "B2B Contact Miner")
   - Описание (например: "Автоматический поиск контактов компаний")
   - Тип использования: Development/Test

4. Примите условия использования

### Шаг 3: Получение credentials

После создания проекта вы получите:

1. **Client ID** (идентификатор клиента)
   - Выглядит как: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
   
2. **Client Secret** (секретный ключ)
   - Выглядит как: `yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy`

⚠️ **Важно:** Сохраните Client Secret сразу - он показывается только один раз!

### Шаг 4: Активация доступа

1. В разделе GigaChat найдите кнопку **"Активировать"** или **"Получить доступ"**
2. Подтвердите активацию
3. Дождитесь подтверждения (обычно мгновенно)

---

## Настройка в проекте

### Обновите `.env` файл:

Откройте файл `.env` и замените placeholder'ы на ваши реальные credentials:

```bash
# GigaChat (Sber) - Recommended for Russian!
GIGACHAT_CLIENT_ID=ваш_client_id_здесь
GIGACHAT_CLIENT_SECRET=ваш_client_secret_здесь
USE_GIGACHAT=true
```

**Пример:**
```bash
GIGACHAT_CLIENT_ID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
GIGACHAT_CLIENT_SECRET=z9y8x7w6-v5u4-t3s2-r1q0-p9o8n7m6l5k4
USE_GIGACHAT=true
```

---

## Проверка настройки

### 1. Создайте тестовый скрипт `test_gigachat.py`:

```python
from gigachat import GigaChat
from gigachat.models import Messages, Message
from config.settings import settings

print("Testing GigaChat API...")
print(f"Client ID: {settings.GIGACHAT_CLIENT_ID[:8]}...")

try:
    gc = GigaChat(
        credentials=settings.GIGACHAT_CLIENT_ID,
        client_secret=settings.GIGACHAT_CLIENT_SECRET,
        verify_ssl_certs=False,
        scope="GIGACHAT_API_PERS"
    )
    
    print("\nSending test request...")
    response = gc.chat(
        messages=[Message(role="user", content="Привет! Напиши короткое приветствие.")],
        temperature=0.7,
        max_tokens=50
    )
    
    print("✅ Success!")
    print(f"\nResponse: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check CLIENT_ID and CLIENT_SECRET in .env")
    print("2. Verify account is activated at developers.sber.ru")
    print("3. Check internet connection")
```

### 2. Запустите тест:

```bash
.\venv\Scripts\python.exe test_gigachat.py
```

Должны увидеть приветствие на русском языке!

---

## 💰 Стоимость

### GigaChat:
- **Free tier:** Бесплатно для разработчиков
- **Лимиты:** Достаточно для большинства проектов
- **Для production:** Может потребоваться коммерческая лицензия

**Итого:** $0 для разработки и тестирования! 🎉

---

## 🔧 Troubleshooting

### Ошибка: "Invalid credentials"
- Проверьте, что CLIENT_ID и CLIENT_SECRET скопированы правильно
- Убедитесь, что нет лишних пробелов
- Проверьте статус проекта в Sber Developers

### Ошибка: "Access denied" или "Not activated"
- Убедитесь, что проект активирован
- Проверьте email на наличие письма подтверждения
- Войдите в кабинет и проверьте статус проекта

### Ошибка: "SSL certificate verification failed"
- Это нормально для тестовой среды
- Параметр `verify_ssl_certs=False` решает проблему
- Для production используйте `verify_ssl_certs=True`

### Ошибка: "Rate limit exceeded"
- Подождите немного перед следующим запросом
- Free tier имеет ограничения на количество запросов в минуту
- Для увеличения лимитов обратитесь в поддержку

---

## 📚 Документация

- **Официальная документация:** https://developers.sber.ru/docs/ru/gigachat/overview
- **API Reference:** https://developers.sber.ru/docs/ru/gigachat/api-reference
- **Примеры кода:** https://github.com/ai-forever/gigachat

---

## 🚀 Следующие шаги

1. ✅ Получите CLIENT_ID и CLIENT_SECRET (см. инструкцию выше)
2. ✅ Обновите `.env` файл
3. ✅ Протестируйте подключение (`test_gigachat.py`)
4. ✅ Запустите основной пайплайн:
   ```bash
   .\venv\Scripts\python.exe main.py
   ```

Готово! Ваш B2B Contact Miner теперь использует российскую LLM модель GigaChat! 🇷🇺🎯
