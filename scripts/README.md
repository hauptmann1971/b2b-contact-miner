# Scripts Directory

Utility and operations scripts for B2B Contact Miner. Run from **project root**:

```bash
cd /opt/b2b-contact-miner   # or your clone path
./venv/bin/python scripts/script_name.py
```

Scripts set `PYTHONPATH` via `os.chdir(ROOT)` + `sys.path.insert` (there is no shared `_path_helper`).

---

## Production runtime (not in `scripts/`)

| Entry point | Role |
|-------------|------|
| `main.py` | Contact mining pipeline → MySQL `task_queue` → `workers/db_task_queue.py` |
| `web_server.py` | Flask UI (port 5000) |
| `api_server.py` | FastAPI export API (optional) |
| `monitoring/healthcheck.py` | Health / queue metrics (mounted from `api_server` or standalone) |

---

## Production ops (manual)

Use on the server when debugging queue, SERP, or keywords. Safe to re-run; read script `--help` where available.

### Pipeline & queue

| Script | Purpose |
|--------|---------|
| `run_pipeline_background.sh` | Start `main.py` detached with absolute log path |
| `monitor_workers.py` | Print `task_queue` stats |
| `recover_stale_tasks.py` | Unlock / reset stale running tasks |
| `unblock_orphan_queue_tasks.py` | Unblock tasks whose parent search failed |
| `retry_failed_search_tasks.py` | Re-queue failed `search_keyword` tasks |
| `check_stuck_keywords.py` | Keywords vs pending/running tasks |
| `reconcile_keyword_is_processed.py` | Fix `keywords.is_processed` vs queue state |
| `reset_keywords_for_rerun.py` | Mark keywords pending for another run |

### SERP denylist

| Script | Purpose |
|--------|---------|
| `apply_serp_denylist.py` | Merge DB suggestions into `.env` |
| `suggest_serp_denylist.py` | Print denylist candidates (no write) |
| `seed_serp_denylist_env.py` | Emit `SERP_BLOCKED_HOST_SUFFIXES` JSON for `.env` |
| `pipeline_quality_report.py` | 24h crawl/queue KPIs |

### Metrics & DB hygiene

| Script | Purpose |
|--------|---------|
| `run_metrics_window.py` | DB metrics between `--start` / `--end` timestamps |
| `fix_mysql_autoincrement_ids.py` | Repair AUTO_INCREMENT on core tables |
| `check_contacts.py` | Contact table summary |
| `check_new_records.py` | Recent row counts |
| `debug_recent_contacts.py` | Inspect latest contacts |

### Yandex credentials

| Script | Purpose |
|--------|---------|
| `refresh_yandex_token.py` | Refresh IAM in `.env` |
| `exchange_oauth_token.py` | OAuth → IAM exchange |
| `test_yandex_token.py` | Quick IAM check |
| `test_yandex_search.py` | Yandex Search API smoke test |

Prefer **`getters/`** for first-time IAM setup: `getters/get_iam_from_oauth.py`, `getters/update_iam_token.py` (see [getters/README.md](../getters/README.md)).

---

## Scheduled on server (cron)

**`weekly_maintenance.sh`** — typical cron (Sunday 03:00):

```bash
0 3 * * 0 root /opt/b2b-contact-miner/scripts/weekly_maintenance.sh >> /opt/b2b-contact-miner/logs/weekly_maintenance.log 2>&1
```

Runs: `pipeline_quality_report.py` → `apply_serp_denylist.py` → `unblock_orphan_queue_tasks.py` → `fix_mysql_autoincrement_ids.py`.

**`scheduler.py`** — optional daily pipeline trigger (used by `deploy/start_all.sh` on dev machines).

---

## Deploy & CI helpers

| Script | Purpose |
|--------|---------|
| `deploy_server.ps1` | SSH deploy from Windows |
| `validate_setup.py` | Local dependency / DB / optional Redis check |
| `download_sonar_report.py` | Pull SonarCloud issues → `doc/sonarcloud_reports/` (gitignored) |

GitHub Actions deploy: `.github/workflows/deploy.yml`. Server helper: `deploy/deploy.sh`.

---

## Development & one-off

| Script | Purpose |
|--------|---------|
| `test_async_pipeline.py` | Queue integration smoke |
| `export_flat.py` | Flat CSV export → `contacts_export.csv` (gitignored) |
| `export_for_llm_test.py` | Sample pages for LLM experiments |
| `rewrite_ru_commit_messages.py` | One-time `git filter-branch` helper (legacy commit messages) |

**Smoke / component tests:** [checkers/README.md](../checkers/README.md) (`smoke_pipeline_quality.py`, `run_weekly_smoke.py`, …).

**Keywords & tokens:** [getters/README.md](../getters/README.md).

---

## Related docs

- Index: [doc/README.md](../doc/README.md) (active vs historical)
- Deploy: [doc/DEPLOYMENT_GUIDE.md](../doc/DEPLOYMENT_GUIDE.md), [doc/YANDEX_SEARCH_SETUP.md](../doc/YANDEX_SEARCH_SETUP.md)
- Queue: [doc/DB_TASK_QUEUE_SETUP.md](../doc/DB_TASK_QUEUE_SETUP.md)
