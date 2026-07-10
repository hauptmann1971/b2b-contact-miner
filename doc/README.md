# Documentation index

Central index for `doc/`. **Historical** material lives in [`archive/doc/`](../archive/doc/) (gitignored locally).

**Scripts & ops:** [scripts/README.md](../scripts/README.md)  
**Getters / checkers:** [getters/README.md](../getters/README.md), [checkers/README.md](../checkers/README.md)

**Commit messages:** use **English** in git (project convention).

---

## Active (current stack)

### Architecture

| Doc | Content |
|-----|---------|
| [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) | Short system overview |
| [C4_ARCHITECTURE.md](C4_ARCHITECTURE.md) | C4 diagrams (Mermaid) |
| [HOW_IT_WORKS.md](HOW_IT_WORKS.md) | Plain-language pipeline walkthrough |
| [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) | Tables and fields (incl. multi-tenant) |
| [TASK_QUEUE.md](TASK_QUEUE.md) | MySQL `task_queue` |
| [AUTH_MULTITENANT.md](AUTH_MULTITENANT.md) | Login, roles, tenants, user admin |

### Deploy & runtime

| Doc | Content |
|-----|---------|
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Server deployment |
| [GITHUB_SECRETS_DEPLOY.md](GITHUB_SECRETS_DEPLOY.md) | GitHub Actions secrets |
| [STARTUP_GUIDE.md](STARTUP_GUIDE.md) | Start web + pipeline |
| [WEB_SERVER_GUIDE.md](WEB_SERVER_GUIDE.md) | Flask UI + auth |
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
| [KEYWORDS_GUIDE.md](KEYWORDS_GUIDE.md) | Keywords in DB |
| [CONTACT_EXTRACTION_METHODS.md](CONTACT_EXTRACTION_METHODS.md) | Regex / LLM extraction |
| [HOW_CONTENT_GOES_TO_LLM.md](HOW_CONTENT_GOES_TO_LLM.md) | LLM payload |
| [RUN_TESTS_GUIDE.md](RUN_TESTS_GUIDE.md) | `pytest tests/` |
| [HYBRID_TAG_SYSTEM.md](HYBRID_TAG_SYSTEM.md) | Tags on contacts |
| [NEW_PAGES_GUIDE.md](NEW_PAGES_GUIDE.md) | UI pages map |

### Config files in `doc/`

- `docker-compose.yml` — local MySQL (optional Redis container; app queue is **MySQL**)
- `setup_mysql.sql` — DB bootstrap

---

## Archive

Superseded docs, old migration notes, duplicate quickstarts → [`archive/doc/`](../archive/doc/).  
See [`archive/README.md`](../archive/README.md).

---

## Generated / local only

| Path | Notes |
|------|--------|
| `doc/sonarcloud_reports/` | Output of `scripts/download_sonar_report.py` |
| `archive/` | Local superseded files (see `archive/README.md`) |
| `data/app_settings.json` | Theme default (passwords use `users` table) |

---

## Quick links

- [How it works →](HOW_IT_WORKS.md)
- [Auth & tenants →](AUTH_MULTITENANT.md)
- [Task queue →](TASK_QUEUE.md)
- [Deploy →](DEPLOYMENT_GUIDE.md)
- [Scripts & ops →](../scripts/README.md)
