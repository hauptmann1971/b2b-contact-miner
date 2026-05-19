# Documentation index

Central index for `doc/`. Prefer **Active** docs for production and onboarding. **Historical** docs are kept for context but may describe removed components (Redis queue, self-hosted SonarQube, GigaChat, old `task_worker.py`).

**Scripts & ops:** [scripts/README.md](../scripts/README.md) — production ops, cron, deploy.  
**Getters / checkers:** [getters/README.md](../getters/README.md), [checkers/README.md](../checkers/README.md).

**Commit messages:** use **English** in git (project convention).

---

## Active (current stack)

### Architecture

| Doc | Content |
|-----|---------|
| [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) | Short system overview |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Detailed module flow |
| [C4_ARCHITECTURE.md](C4_ARCHITECTURE.md) | C4 diagrams (compare with real `services/` paths) |
| [HOW_IT_WORKS.md](HOW_IT_WORKS.md) | Plain-language pipeline walkthrough |
| [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) | Tables and fields |
| [DB_TASK_QUEUE_SETUP.md](DB_TASK_QUEUE_SETUP.md) | MySQL `task_queue`, workers |

### Deploy & runtime

| Doc | Content |
|-----|---------|
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Server deployment |
| [GITHUB_SECRETS_DEPLOY.md](GITHUB_SECRETS_DEPLOY.md) | GitHub Actions secrets |
| [STARTUP_GUIDE.md](STARTUP_GUIDE.md) | Start web + pipeline |
| [WEB_SERVER_GUIDE.md](WEB_SERVER_GUIDE.md) | Flask UI |
| [WEB_SERVER_QUICKSTART.md](WEB_SERVER_QUICKSTART.md) | Quick UI start |
| [MONITORING_GUIDE.md](MONITORING_GUIDE.md) | Health, metrics, alerts |
| [MONITORING_CHEATSHEET.md](MONITORING_CHEATSHEET.md) | Command cheat sheet |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Common commands |

### Configuration

| Doc | Content |
|-----|---------|
| [API_KEYS_SETUP.md](API_KEYS_SETUP.md) | API keys overview |
| [YANDEXGPT_SETUP.md](YANDEXGPT_SETUP.md) | YandexGPT / IAM |
| [YANDEX_SEARCH_SETUP.md](YANDEX_SEARCH_SETUP.md) | Yandex Search API (prod SERP) |
| [SONARCLOUD_SETUP.md](SONARCLOUD_SETUP.md) | SonarCloud CI |
| [MYSQL_SETUP.md](MYSQL_SETUP.md) | MySQL |
| [DOCKER_SETUP.md](DOCKER_SETUP.md) | Docker MySQL (optional) |
| [INSTALL_DEPS.md](INSTALL_DEPS.md) | Python dependencies |

### Usage

| Doc | Content |
|-----|---------|
| [KEYWORDS_GUIDE.md](KEYWORDS_GUIDE.md) | Keywords in DB — note: auto-translation in guide is **not** wired in `add_keyword` yet |
| [CONTACT_EXTRACTION_METHODS.md](CONTACT_EXTRACTION_METHODS.md) | Regex / LLM extraction |
| [HOW_CONTENT_GOES_TO_LLM.md](HOW_CONTENT_GOES_TO_LLM.md) | LLM payload |
| [RUN_TESTS_GUIDE.md](RUN_TESTS_GUIDE.md) | `pytest tests/` |
| [HYBRID_TAG_SYSTEM.md](HYBRID_TAG_SYSTEM.md) | Tags on contacts |
| [NEW_PAGES_GUIDE.md](NEW_PAGES_GUIDE.md) | UI pages |

### Config files in `doc/`

- `docker-compose.yml` — local MySQL (+ optional Redis container; app queue is **MySQL**, not Redis)
- `setup_mysql.sql` — DB bootstrap

---

## Historical (archive)

May reference **Redis task queue**, **self-hosted SonarQube**, **GigaChat**, or **`workers/task_worker.py`** — no longer used.

| Doc | Why archived |
|-----|----------------|
| [SONARQUBE_SETUP.md](SONARQUBE_SETUP.md) | Self-hosted SonarQube → use SonarCloud |
| `sonarqube-docker-compose.yml` | Same |
| [REDIS_SETUP.md](REDIS_SETUP.md) | Queue moved to MySQL `task_queue` |
| [ASYNC_PIPELINE_MIGRATION.md](ASYNC_PIPELINE_MIGRATION.md) | Migration notes (done) |
| [MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md) | Migration completion note |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | Old implementation log |
| [БЫСТРЫЙ_СТАРТ_ASYNC.md](БЫСТРЫЙ_СТАРТ_ASYNC.md) | Old async quick start |
| [БЫСТРЫЙ_СТАРТ.md](БЫСТРЫЙ_СТАРТ.md) | Superseded by STARTUP_GUIDE |
| [GIGACHAT_SETUP.md](GIGACHAT_SETUP.md) | GigaChat not in current code |
| [SETUP_COMPLETE.md](SETUP_COMPLETE.md) | One-time setup snapshot |
| [VENV_SETUP_REPORT.md](VENV_SETUP_REPORT.md) | Old venv report |
| [TEST_REPORT.md](TEST_REPORT.md) | Old test snapshot |
| [STARTUP_IMPROVEMENTS.md](STARTUP_IMPROVEMENTS.md) | Old improvement notes |
| [IMPROVEMENTS.md](IMPROVEMENTS.md) | Old improvement list |
| [README_УЛУЧШЕНИЯ.md](README_УЛУЧШЕНИЯ.md) | Old improvements (RU) |
| [FINAL_STEPS.md](FINAL_STEPS.md) | Old checklist |
| [QUICKSTART_VENV.md](QUICKSTART_VENV.md) | Overlaps STARTUP_GUIDE |
| [STARTUP_SCRIPTS_GUIDE.md](STARTUP_SCRIPTS_GUIDE.md) | `deploy/start_all*` (dev convenience) |
| [RELIABILITY_IMPROVEMENTS.md](RELIABILITY_IMPROVEMENTS.md) | Design notes (partially implemented) |
| [DIAGRAMS.md](DIAGRAMS.md) | Extra diagrams — verify against code |
| [LLM_PROMPT_EXAMPLE.md](LLM_PROMPT_EXAMPLE.md) | Example only |
| [FIX_YANDEXGPT_403.md](FIX_YANDEXGPT_403.md) | Troubleshooting snapshot |
| [CHANGELOG.md](CHANGELOG.md) | Changelog (not always updated) |

---

## Generated / local only

| Path | Notes |
|------|--------|
| `doc/sonarcloud_reports/` | Output of `scripts/download_sonar_report.py` (in `.gitignore`) |

---

## Quick links

- [How it works →](HOW_IT_WORKS.md)
- [Deploy →](DEPLOYMENT_GUIDE.md)
- [Yandex SERP →](YANDEX_SEARCH_SETUP.md)
- [Scripts & ops →](../scripts/README.md)
- [Run tests →](RUN_TESTS_GUIDE.md)
