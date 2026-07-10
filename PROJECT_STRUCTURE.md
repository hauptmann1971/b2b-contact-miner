# B2B Contact Miner — Project Structure

> **Doc index:** [doc/README.md](doc/README.md)  
> **Architecture:** [doc/HOW_IT_WORKS.md](doc/HOW_IT_WORKS.md), [doc/C4_ARCHITECTURE.md](doc/C4_ARCHITECTURE.md)  
> **Auth:** [doc/AUTH_MULTITENANT.md](doc/AUTH_MULTITENANT.md)

## Root layout

```
b2b-contact-miner/
├── main.py                 # Pipeline: enqueue search_keyword, run DB workers
├── web_server.py           # Flask app (registers routes/)
├── api_server.py           # Optional FastAPI export API + mounts /health
├── requirements.txt
├── .env.example
├── sonar-project.properties
│
├── config/
│   └── settings.py         # Pydantic settings from .env
│
├── models/
│   ├── database.py         # SQLAlchemy models (keywords, contacts, …)
│   ├── tenant.py           # tenants, users, roles
│   ├── task_queue.py       # task_queue table model
│   └── schemas.py          # Pydantic DTOs
│
├── services/
│   ├── serp_service.py
│   ├── crawler_service.py
│   ├── extraction_service.py
│   ├── keyword_service.py
│   ├── export_service.py
│   ├── translation_service.py
│   ├── auth_service.py
│   ├── tenant_bootstrap.py
│   └── user_admin_service.py
│
├── workers/
│   └── db_task_queue.py    # MySQL-backed async workers + handlers
│
├── routes/
│   ├── user_routes.py
│   ├── auth_routes.py
│   ├── admin_routes.py
│   ├── api_routes.py
│   └── health_routes.py
│
├── utils/                  # SERP filters, http_fetch, web_security, tenant_context, …
├── monitoring/
│   └── healthcheck.py      # FastAPI health / queue metrics (:8000)
│
├── templates/              # Jinja2 HTML
├── static/                 # CSS / JS
│
├── scripts/                # Ops, cron, exports — see scripts/README.md
├── getters/                # CLI: add keywords, view results
├── checkers/               # Smoke / manual checks — checkers/README.md
├── tests/                  # pytest suite
├── migrations/             # SQL + apply_*.py
├── deploy/                 # nginx, start_all*, deploy.sh
├── doc/                    # Active documentation
└── archive/                # Superseded local files (gitignored, see archive/README.md)
```

There is **no** `src/` package — modules live at repo root (PYTHONPATH = project root).

## Runtime processes

| Process | Entry | Notes |
|---------|--------|--------|
| Web UI | `python web_server.py` | `:5000`, localhost; Nginx on prod |
| Pipeline | `python main.py` | Starts `DatabaseTaskQueue` workers in same process |
| Health API | `uvicorn monitoring.healthcheck:app` or `api_server.py` | Optional `:8000` |
| Scheduler | `python scripts/scheduler.py` | Daily `run_pipeline()` |

Task queue is **MySQL** (`task_queue` table), not Redis.

## CI

| Workflow | Purpose |
|----------|---------|
| `.github/workflows/tests.yml` | `pytest tests/` |
| `.github/workflows/sonarcloud.yml` | SonarCloud analysis |
| `.github/workflows/deploy.yml` | Manual SSH deploy (workflow_dispatch) |

## Quick links

- [How it works](doc/HOW_IT_WORKS.md)
- [Auth & tenants](doc/AUTH_MULTITENANT.md)
- [Task queue](doc/TASK_QUEUE.md)
- [Scripts](scripts/README.md)
- [Run tests](doc/RUN_TESTS_GUIDE.md)
