# 🔧 Исправление ошибки 403 Forbidden для YandexGPT

## Проблема:
Получена ошибка `403 Client Error: Forbidden` при попытке использовать YandexGPT.

## Причина:
У вашего аккаунта нет прав на использование YandexGPT API.

---

## ✅ Решение: Добавить роль ai.languageModels.user

### Способ 1: Через веб-консоль (рекомендуется)

1. **Перейдите в консоль Yandex Cloud:**
   https://console.cloud.yandex.ru/

2. **Выберите ваш каталог (folder):**
   - Нажмите на название каталога в верхней панели
   - Или выберите из списка каталогов

3. **Перейдите в раздел "Доступ":**
   - В меню слева выберите **"Доступ"** (Access)
   - Или нажмите вкладку **"Доступ"** в верхней части страницы

4. **Добавьте роль:**
   - Нажмите кнопку **"Добавить пользователей"** или **"Добавить субъект"**
   - В поле поиска введите ваш email или имя пользователя
   - Выберите вашего пользователя из списка
   
5. **Назначьте роль:**
   - В выпадающем списке ролей выберите **"ai.languageModels.user"**
   - Или найдите её через поиск
   - Нажмите **"Сохранить"** или **"Добавить"**

6. **Подождите 1-2 минуты** для применения изменений

7. **Повторно получите IAM токен:**
   ```bash
   python get_iam_from_oauth.py
   ```
   (IAM токены живут только 12 часов)

8. **Протестируйте подключение:**
   ```bash
   python test_yandexgpt.py
   ```

---

### Способ 2: Через CLI (если установлен yc)

```bash
# Добавить роль пользователю
yc resource-manager folder add-access-binding b1g7f8h9j0k1l2m3n4o5 \
  --role ai.languageModels.user \
  --subject userAccount:ваш_user_id

# Получить ваш user_id
yc iam whoami
```

---

## 📋 Проверка после добавления роли

1. **Обновите IAM токен** (старый может не иметь новых прав):
   ```bash
   python get_iam_from_oauth.py
   ```

2. **Протестируйте подключение:**
   ```bash
   python test_yandexgpt.py
   ```

3. **Если всё работает**, запустите основной пайплайн:
   ```bash
   python main.py
   ```

---

## ⚠️ Важные моменты

### IAM токен живет 12 часов!
- После получения нового IAM токена старые права могут не примениться
- Всегда получайте новый токен после изменения ролей
- Для production настройте автоматическое обновление токенов

### Billing account должен быть активен
- Убедитесь, что у вас есть активный платежный аккаунт
- Новые пользователи получают грант 4000₽
- Проверьте статус в разделе "Billing" консоли

### Folder ID должен быть правильным
- Текущий Folder ID: `b1g7f8h9j0k1l2m3n4o5`
- Если это тестовый ID, замените его на реальный из вашей консоли
- Найти можно в консоли: https://console.cloud.yandex.ru/

---

## 🔍 Диагностика

### Проверить текущие роли:
```bash
yc resource-manager folder list-access-bindings b1g7f8h9j0k1l2m3n4o5
```

### Проверить статус billing:
1. Перейдите в https://console.cloud.yandex.ru/billing
2. Убедитесь, что статус "Активен"
3. Проверьте наличие гранта или привязанной карты

### Проверить доступность сервиса:
```bash
curl -X POST \
  "https://llm.api.cloud.yandex.net/foundationModels/v1/completion" \
  -H "Authorization: Bearer ВАШ_IAM_TOKEN" \
  -H "x-folder-id: ВАШ_FOLDER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "modelUri": "gpt://ВАШ_FOLDER_ID/yandexgpt/latest",
    "completionOptions": {
      "stream": false,
      "temperature": 0.7,
      "maxTokens": "50"
    },
    "messages": [
      {"role": "user", "text": "Привет"}
    ]
  }'
```

---

## 📞 Поддержка

Если проблема сохраняется:
1. Проверьте документацию: https://cloud.yandex.ru/docs/yandexgpt/
2. Обратитесь в поддержку Yandex Cloud
3. Проверьте логи в разделе "Аудит" консоли

---

## ✅ Чеклист

- [ ] Роль `ai.languageModels.user` добавлена
- [ ] Получен новый IAM токен
- [ ] Folder ID правильный
- [ ] Billing account активен
- [ ] Тест `test_yandexgpt.py` проходит успешно
