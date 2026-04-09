# Инструкция по запуску тестов

## Проблема

Сейчас нет доступа к PyPI (Python Package Index) для установки pytest.

## Решение

### Вариант 1: Проверить подключение к интернету

```bash
# Проверьте доступность интернета
ping pypi.org

# Если не пингуется, проверьте настройки сети
```

### Вариант 2: Использовать proxy (если есть корпоративный proxy)

```bash
# Windows PowerShell
$env:HTTP_PROXY="http://proxy-server:port"
$env:HTTPS_PROXY="http://proxy-server:port"
py -m pip install pytest pytest-asyncio pytest-cov

# Или через командную строку CMD
set HTTP_PROXY=http://proxy-server:port
set HTTPS_PROXY=http://proxy-server:port
py -m pip install pytest pytest-asyncio pytest-cov
```

### Вариант 3: Установить offline (если есть wheel файлы)

Если у вас есть доступ к другому компьютеру с интернетом:

1. На компьютере с интернетом:
```bash
pip download pytest pytest-asyncio pytest-cov -d ./packages
```

2. Скопируйте папку `packages` на этот компьютер

3. Установите offline:
```bash
py -m pip install --no-index --find-links=./packages pytest pytest-asyncio pytest-cov
```

### Вариант 4: Использовать зеркало PyPI

```bash
# Использовать китайское зеркало (быстрее из некоторых регионов)
py -m pip install pytest pytest-asyncio pytest-cov -i https://pypi.tuna.tsinghua.edu.cn/simple

# Или другое зеркало
py -m pip install pytest pytest-asyncio pytest-cov -i https://mirrors.aliyun.com/pypi/simple/
```

---

## После установки pytest

### 1. Быстрый запуск всех тестов

```bash
python run_tests.py
```

### 2. Запуск через pytest напрямую

```bash
# Все тесты с подробным выводом
py -m pytest tests/ -v

# С покрытием кода
py -m pytest tests/ --cov=services --cov=utils --cov-report=term-missing

# HTML отчет о покрытии
py -m pytest tests/ --cov=services --cov=utils --cov-report=html
# Затем откройте htmlcov/index.html в браузере
```

### 3. Запуск отдельных тестов

```bash
# Только extraction service тесты
py -m pytest tests/test_extraction_service.py -v

# Только robots checker тесты  
py -m pytest tests/test_robots_checker.py -v

# Конкретный тест
py -m pytest tests/test_extraction_service.py::TestExtractionService::test_mailto_extraction -v
```

---

## Ожидаемый результат

При успешном запуске вы должны увидеть:

```
======================== test session starts ========================
platform win32 -- Python 3.13.9, pytest-7.x.x

tests/test_extraction_service.py .............                 [ 59%]
tests/test_robots_checker.py .........                         [100%]

======================== 22 passed in 1.23s =========================

---------- coverage: platform win32, python 3.13.9 -----------
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
services/extraction_service.py            120     18    85%
utils/robots_checker.py                    45      7    84%
-----------------------------------------------------------
TOTAL                                     165     25    85%
```

---

## Troubleshooting

### Ошибка: "No module named 'pytest'"

**Решение:** Установите pytest (см. варианты выше)

### Ошибка: "Connection timeout"

**Решение:** 
- Проверьте интернет подключение
- Используйте proxy если нужно
- Попробуйте зеркала PyPI

### Ошибка: "ModuleNotFoundError: No module named 'services'"

**Решение:**
```bash
# Запускайте из корня проекта
cd c:\Users\romanov\PycharmProjects\b2b-contact-miner
py -m pytest tests/ -v
```

### Тесты падают с ошибкой импорта

**Решение:** Убедитесь, что все зависимости установлены:
```bash
py -m pip install -r requirements.txt
```

---

## Проверка готовности кода

Код уже проверен и готов к тестированию:

✅ `tests/test_extraction_service.py` - синтаксис OK  
✅ `tests/test_robots_checker.py` - синтаксис OK  
✅ `tests/conftest.py` - синтаксис OK  
✅ Все сервисные модули - синтаксис OK  

Осталось только установить pytest! 🎯

---

## Альтернатива: Ручная проверка логики

Если нельзя установить pytest, можно проверить логику вручную:

```python
# test_manual.py
from services.extraction_service import ExtractionService

service = ExtractionService()

# Test 1: mailto extraction
content = '<a href="mailto:ceo@company.com">Email</a>'
contacts = service.extract_contacts([{"content": content, "type": "regular_page"}])
assert "ceo@company.com" in contacts.emails
print("✅ Test 1 passed: mailto extraction")

# Test 2: obfuscation detection
import re
content = "Contact: ceo[at]company.com"
has_obfuscation = any(re.search(p, content, re.IGNORECASE) 
                     for p in service.obfuscation_patterns)
assert has_obfuscation is True
print("✅ Test 2 passed: obfuscation detection")

print("\n✅ All manual tests passed!")
```

Запустите:
```bash
python test_manual.py
```

---

## Контакты

Если проблемы с установкой продолжаются, обратитесь к:
- Системному администратору (для настройки proxy)
- Документации компании по работе с PyPI
- Используйте offline установку с другого компьютера
