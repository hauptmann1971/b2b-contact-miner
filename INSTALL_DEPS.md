# Необходимые зависимости для запуска тестов

## Статус установленных пакетов

### ✅ Уже установлено:
- SQLAlchemy 2.0.48
- PyMySQL 1.1.2
- python-dotenv 1.2.2
- tenacity 8.2.3

### ❌ Необходимо установить для тестов:

#### Критические (обязательные):
```bash
py -m pip install pydantic==2.5.0 pydantic-settings==2.1.0
```

#### Для extraction_service тестов:
```bash
py -m pip install email-validator==2.1.0 dnspython==2.4.2
```

#### Для robots_checker тестов:
```bash
# Не требует дополнительных зависимостей
```

#### Для запуска pytest:
```bash
py -m pip install pytest==7.4.4 pytest-asyncio==0.23.3 pytest-cov==4.1.0
```

---

## Полная команда установки

### Вариант 1: Установить всё сразу (рекомендуется)

```bash
py -m pip install pydantic==2.5.0 pydantic-settings==2.1.0 email-validator==2.1.0 dnspython==2.4.2 pytest==7.4.4 pytest-asyncio==0.23.3 pytest-cov==4.1.0
```

### Вариант 2: Установить по частям

```bash
# Шаг 1: Core dependencies
py -m pip install pydantic==2.5.0 pydantic-settings==2.1.0

# Шаг 2: Email validation
py -m pip install email-validator==2.1.0 dnspython==2.4.2

# Шаг 3: Testing framework
py -m pip install pytest==7.4.4 pytest-asyncio==0.23.3 pytest-cov==4.1.0
```

### Вариант 3: Установить все зависимости проекта

```bash
py -m pip install -r requirements.txt
```

⚠️ **Внимание:** Это установит ~50 пакетов, включая Playwright, OpenAI, FastAPI и др.

---

## Минимальный набор ТОЛЬКО для тестов

Если хотите установить минимум для запуска 22 тестов:

```bash
py -m pip install ^
    pydantic==2.5.0 ^
    pydantic-settings==2.1.0 ^
    email-validator==2.1.0 ^
    dnspython==2.4.2 ^
    pytest==7.4.4 ^
    pytest-asyncio==0.23.3 ^
    pytest-cov==4.1.0
```

**PowerShell (одной строкой):**
```powershell
py -m pip install pydantic==2.5.0 pydantic-settings==2.1.0 email-validator==2.1.0 dnspython==2.4.2 pytest==7.4.4 pytest-asyncio==0.23.3 pytest-cov==4.1.0
```

---

## После установки

### 1. Проверьте установку

```bash
py -m pytest --version
py -c "import pydantic; print(f'Pydantic {pydantic.__version__}')"
py -c "import dns.resolver; print('dnspython OK')"
```

### 2. Запустите тесты

```bash
# Все тесты
py -m pytest tests/ -v

# С покрытием
py -m pytest tests/ --cov=services --cov=utils --cov-report=term-missing

# Или через скрипт
python run_tests.py
```

---

## Если проблемы с сетью

### Используйте зеркала PyPI:

```bash
# Китайское зеркало (быстрее)
py -m pip install pydantic==2.5.0 pydantic-settings==2.1.0 email-validator==2.1.0 dnspython==2.4.2 pytest==7.4.4 pytest-asyncio==0.23.3 pytest-cov==4.1.0 -i https://pypi.tuna.tsinghua.edu.cn/simple

# Aliyun зеркало
py -m pip install pydantic==2.5.0 pydantic-settings==2.1.0 email-validator==2.1.0 dnspython==2.4.2 pytest==7.4.4 pytest-asyncio==0.23.3 pytest-cov==4.1.0 -i https://mirrors.aliyun.com/pypi/simple/
```

### Или настройте proxy:

```powershell
$env:HTTP_PROXY="http://proxy-server:port"
$env:HTTPS_PROXY="http://proxy-server:port"
py -m pip install pydantic==2.5.0 pydantic-settings==2.1.0 email-validator==2.1.0 dnspython==2.4.2 pytest==7.4.4 pytest-asyncio==0.23.3 pytest-cov==4.1.0
```

---

## Альтернатива: Ручные тесты без pytest

Если не можете установить pytest, используйте `test_manual.py`:

**Требуется только:**
```bash
py -m pip install pydantic==2.5.0 pydantic-settings==2.1.0 email-validator==2.1.0 dnspython==2.4.2
```

**Запуск:**
```bash
python test_manual.py
```

Это запустит 10 тестов без pytest!

---

## Проверка готовности

После установки выполните:

```bash
# Проверка синтаксиса всех модулей
py -c "import py_compile; files = ['config/settings.py', 'models/database.py', 'services/extraction_service.py', 'utils/robots_checker.py']; [py_compile.compile(f, doraise=True) for f in files]; print('✅ All modules syntax OK')"

# Проверка импортов
py -c "from services.extraction_service import ExtractionService; print('✅ ExtractionService imported')"
py -c "from utils.robots_checker import RobotsChecker; print('✅ RobotsChecker imported')"
```

Если все команды прошли успешно - можно запускать тесты! 🎉

---

## Итоговый чеклист

- [ ] Установлен Python 3.13.9 ✅
- [ ] Установлен SQLAlchemy ✅
- [ ] Установлен PyMySQL ✅
- [ ] Установлен python-dotenv ✅
- [ ] Установлен pydantic ⏳
- [ ] Установлен pydantic-settings ⏳
- [ ] Установлен email-validator ⏳
- [ ] Установлен dnspython ⏳
- [ ] Установлен pytest ⏳
- [ ] Установлен pytest-asyncio ⏳
- [ ] Установлен pytest-cov ⏳

После установки всех отмеченных ⏳ пакетов можно запускать тесты!
