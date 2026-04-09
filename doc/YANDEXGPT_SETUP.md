# Инструкция по настройке YandexGPT

## 🎯 YandexGPT от Яндекса - Отличный выбор для русского языка!

---

## Что такое YandexGPT?

YandexGPT - это большая языковая модель от Яндекса, отлично понимающая русский язык.

### Преимущества:
- ✅ Отличное понимание русского языка
- ✅ Высокое качество генерации
- ✅ Надежная инфраструктура Яндекса
- ✅ Российская разработка (нет проблем с доступом)
- ✅ Хорошая документация

### Стоимость:
- 💰 **Free tier:** Есть пробный период с бесплатными токенами
- 💰 **После trial:** ~$0.05-0.10 за 1M tokens (очень дешево!)

---

## Как получить credentials:

### Шаг 1: Регистрация в Yandex Cloud

1. **Перейдите на:** https://cloud.yandex.ru/
2. Нажмите **"Войти"** или **"Зарегистрироваться"**
3. Зарегистрируйтесь через:
   - Яндекс ID (если есть)
   - Email
   - Социальные сети

### Шаг 2: Создание платежного аккаунта

1. После входа создайте **платежный аккаунт**
2. Привяжите карту (для верификации)
3. Получите **грант на 4000₽** для новых пользователей (хватит надолго!)

### Шаг 3: Создание облака и каталога

1. В консоли Yandex Cloud нажмите **"Создать облако"**
2. Дайте имя (например: "b2b-miner")
3. Внутри облака создайте **каталог** (folder)
4. **Скопируйте Folder ID** (выглядит как: `b1gxxxxxxxxxxxx`)

### Шаг 4: Создание сервисного аккаунта

1. Перейдите в раздел **"Сервисные аккаунты"**
2. Нажмите **"Создать сервисный аккаунт"**
3. Дайте имя (например: "gpt-service")
4. Назначьте роль **"ai.languageModels.user"**

### Шаг 5: Создание IAM токена

Есть два способа:

#### Способ A: Через CLI (рекомендуется)

1. Установите Yandex Cloud CLI:
   ```bash
   pip install yandexcloud
   ```

2. Авторизуйтесь:
   ```bash
   yc init
   ```

3. Создайте токен:
   ```bash
   yc iam create-token
   ```

4. Скопируйте полученный токен (длинная строка)

#### Способ B: Через веб-интерфейс

1. Перейдите в сервисный аккаунт
2. Нажмите **"Создать авторизованный ключ"**
3. Скачайте файл с ключом
4. Используйте его для получения IAM токена

⚠️ **Важно:** IAM токен живет 12 часов! Для production нужно автоматическое обновление.

---

## Настройка в проекте

### Обновите `.env` файл:

Откройте файл `.env` и замените placeholder'ы на ваши реальные credentials:

```bash
# YandexGPT
YANDEX_IAM_TOKEN=ваш_iam_токен_здесь
YANDEX_FOLDER_ID=b1gxxxxxxxxxxxx
USE_YANDEXGPT=true
```

**Пример:**
```bash
YANDEX_IAM_TOKEN=t1.9euelZqRl5m...
YANDEX_FOLDER_ID=b1g7f8h9j0k1l2m3n4o5
USE_YANDEXGPT=true
```

---

## Проверка настройки

### 1. Создайте тестовый скрипт `test_yandexgpt.py`:

```python
import requests
from config.settings import settings

print("Testing YandexGPT API...")
print(f"Folder ID: {settings.YANDEX_FOLDER_ID}")
print(f"IAM Token: {settings.YANDEX_IAM_TOKEN[:10]}...")

url = f"https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {settings.YANDEX_IAM_TOKEN}",
    "x-folder-id": settings.YANDEX_FOLDER_ID
}

payload = {
    "modelUri": f"gpt://{settings.YANDEX_FOLDER_ID}/yandexgpt/latest",
    "completionOptions": {
        "stream": False,
        "temperature": 0.7,
        "maxTokens": "50"
    },
    "messages": [
        {"role": "user", "text": "Привет! Напиши короткое приветствие."}
    ]
}

try:
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    result = response.json()
    text = result["result"]["alternatives"][0]["message"]["text"]
    
    print("\n✅ Success!")
    print(f"\nResponse: {text}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check IAM_TOKEN and FOLDER_ID in .env")
    print("2. Verify service account has ai.languageModels.user role")
    print("3. Check if IAM token expired (lives 12 hours)")
    print("4. Verify billing account is active")
```

### 2. Запустите тест:

```bash
.\venv\Scripts\python.exe test_yandexgpt.py
```

Должны увидеть приветствие на русском языке!

---

## ⚠️ Важно: Обновление IAM токена

IAM токен живет только 12 часов. Для production используйте один из способов:

### Вариант 1: Автоматическое обновление через CLI

```python
import subprocess

def get_new_iam_token():
    result = subprocess.run(['yc', 'iam', 'create-token'], 
                          capture_output=True, text=True)
    return result.stdout.strip()
```

### Вариант 2: Использовать API ключ вместо IAM токена

Создайте长期 API ключ для сервисного аккаунта.

---

## 💰 Стоимость

### YandexGPT:
- **Trial period:** 4000₽ грант для новых пользователей
- **После trial:** ~$0.05-0.10 за 1M tokens
- **Для проекта:** При обработке obfuscated emails: ~$0.01-0.05/run

**Итого:** Очень недорого, особенно с грантом! 🎉

---

## 🔧 Troubleshooting

### Ошибка: "Invalid authentication credentials"
- IAM токен истек (живет 12 часов)
- Создайте новый токен: `yc iam create-token`
- Обновите `.env`

### Ошибка: "Permission denied"
- Проверьте, что у сервисного аккаунта есть роль `ai.languageModels.user`
- Добавьте роль в консоли Yandex Cloud

### Ошибка: "Billing account not found"
- Активируйте платежный аккаунт
- Привяжите карту
- Получите грант 4000₽

### Ошибка: "Folder not found"
- Проверьте Folder ID в консоли
- Убедитесь, что каталог существует

---

## 📚 Документация

- **Официальная документация:** https://cloud.yandex.ru/docs/yandexgpt/
- **API Reference:** https://cloud.yandex.ru/docs/yandexgpt/api-ref/
- **Примеры кода:** https://github.com/yandex-cloud/python-sdk

---

## 🚀 Следующие шаги

1. ✅ Зарегистрируйтесь в Yandex Cloud
2. ✅ Создайте сервисный аккаунт и получите IAM токен
3. ✅ Скопируйте Folder ID
4. ✅ Обновите `.env` файл
5. ✅ Протестируйте подключение (`test_yandexgpt.py`)
6. ✅ Запустите основной пайплайн:
   ```bash
   .\venv\Scripts\python.exe main.py
   ```

Готово! Ваш B2B Contact Miner теперь использует YandexGPT! 🇷🇺🎯
