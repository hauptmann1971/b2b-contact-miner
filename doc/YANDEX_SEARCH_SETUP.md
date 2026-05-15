# Yandex Search API (SERP) для b2b-contact-miner

Поиск в проде: `SERP_API_PROVIDER=yandex`. Тот же **Folder ID** и **IAM** (OAuth), что для YandexGPT.

## Почему в консоли «нет сервиса Search API»

Отдельной кнопки «Подключить Search API» в каталоге часто **нет**. Достаточно:

1. Биллинг на облаке (у вас OK).
2. Роль **`search-api.webSearch.user`** на **каталоге** (folder).
3. IAM-токен того же субъекта, что и для GPT.

Документация: [Yandex Search API](https://yandex.cloud/en/docs/search-api/).

## Шаг 1 — роль на каталоге (консоль)

1. [console.yandex.cloud](https://console.yandex.cloud/) → каталог с `YANDEX_FOLDER_ID`.
2. **Права доступа** / **Access bindings** → **Назначить роли**.
3. Субъект: **ваш пользователь** (тот же аккаунт, с которого взят `YANDEX_OAUTH_TOKEN`), не обязательно сервисный аккаунт.
4. Роль: в поиске введите `search` → **`search-api.webSearch.user`** (Пользователь веб-поиска).
5. Сохранить.

## Шаг 2 — проверка (на сервере)

```bash
cd /opt/b2b-contact-miner
# при необходимости обновить IAM из OAuth
./venv/bin/python scripts/test_yandex_search.py
```

- **200 + список URL** — можно ставить `SERP_API_PROVIDER=yandex` в проде.
- **403 Forbidden** — роль не на том субъекте или не на том folder.
- **404** — проверьте `YANDEX_FOLDER_ID`.

## Шаг 3 — прод (.env на сервере)

```env
SERP_API_PROVIDER=yandex
# уже есть:
YANDEX_FOLDER_ID=...
YANDEX_IAM_TOKEN=...
YANDEX_OAUTH_TOKEN=...
AUTO_REFRESH_YANDEX_IAM_BEFORE_RUN=true
```

Dev локально: `SERP_API_PROVIDER=duckduckgo`.

## CLI (альтернатива консоли)

```bash
yc config set folder-id <FOLDER_ID>
yc iam user-account get --login your@email
yc resource-manager folder add-access-binding <FOLDER_ID> \
  --role search-api.webSearch.user \
  --subject userAccount:<USER_ACCOUNT_ID>
```

## Страны

В коде: `RU` → yandex.ru, `KZ` → yandex.kz, `UZ` → yandex.uz, `BY` → yandex.by; остальные CIS → `SEARCH_TYPE_RU`.

## Оплата

Search API тарифицируется отдельно от YandexGPT. Смотрите [тарифы](https://yandex.cloud/en/docs/search-api/pricing).
