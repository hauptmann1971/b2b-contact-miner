# How the project works

> **Updated for current code** (DB task queue, configurable SERP). See also [TASK_QUEUE.md](TASK_QUEUE.md), [scripts/README.md](../scripts/README.md).

## Summary

**B2B Contact Miner** finds B2B contacts by:

1. Loading pending rows from `keywords`
2. Enqueueing `search_keyword` tasks → SERP (`SERP_API_PROVIDER`: `yandex` / `duckduckgo` / `serpapi`)
3. Crawling selected URLs (`crawl_domain`)
4. Extracting contacts (`extract_contacts`) — regex / JSON-LD first, LLM fallback
5. Storing results in MySQL

---

## Project layout

```
main.py                     # Pipeline orchestrator
web_server.py               # Flask UI
workers/db_task_queue.py    # Async workers + MySQL task_queue
services/
  serp_service.py           # Search
  crawler_service.py          # HTTP-first + Playwright
  extraction_service.py       # Contacts + optional LLM
models/database.py          # ORM tables
```

---

## Step 1: Add keywords

**Web UI:** `web_server.py` → form on `/` (one `language` + `country` per row).

**CLI:**

```bash
python getters/add_keywords.py
python getters/add_keywords.py show
```

Each row: `keyword`, `language`, `country`. The DB has `UNIQUE(keyword)` on text only — do not rely on duplicate text with different locales unless you change the schema.

---

## Step 2: Run pipeline

```bash
python main.py
# or on server:
./scripts/run_pipeline_background.sh
```

**What `run_pipeline()` does:**

1. Preflight (SERP / LLM settings)
2. `DatabaseTaskQueue(max_concurrent=settings.MAX_CONCURRENT_DOMAINS)` — default **12** workers
3. For each pending keyword → `add_task(task_type='search_keyword', ...)`
4. Workers process the queue until keywords are done or timeout (`_wait_for_completion`, default 2h)
5. Optional nightly quality gate (`NIGHTLY_FAIL_ON_QUALITY_GATE`)

Legacy sync path `_process_keyword()` in `main.py` is **not** used here (only `getters/run_specific_keyword.py`).

---

## Step 3: Search (`search_keyword`)

Worker calls `SerpService.search()` with:

- `build_search_query(keyword, language, country)` — adds locale hints (`контакты email`, etc.)
- `num_results=settings.SEARCH_RESULTS_PER_KEYWORD` — default **5**
- Results filtered (`SERP_BLOCKED_HOST_SUFFIXES`), deduped, top URLs picked for crawl

SERP rows saved in `search_results` inside this task (not a separate `save_results` worker).

---

## Step 4: Crawl (`crawl_domain`)

- Optional skip: snippet already has email/Telegram (`SERP_SNIPPET_SKIP_CRAWL`)
- HTTP fetch first (`HTTP_FETCH_ENABLED`), then Playwright if needed
- `MAX_PAGES_PER_DOMAIN` (default 3), wall-clock cap `DOMAIN_CRAWL_TIMEOUT`
- Denylist / scoring: `utils/serp_filters.py`

---

## Step 5: Extract (`extract_contacts`)

- Regex, JSON-LD, mailto links
- LLM if enabled: `USE_YANDEXGPT` / `USE_DEEPSEEK` / `USE_OPENAI` (see `extraction_service.py`)
- MX check on emails; optional skip empty domains (`SAVE_EMPTY_DOMAIN_CONTACTS`)

---

## Step 6: View results

- Web: `/contacts`, `/keywords`
- CLI: `python getters/view_results.py`, `python getters/check_db_raw.py`
- Export: Flask route or `scripts/export_flat.py` → `contacts_export.csv` (gitignored)

---

## Key `.env` settings

```bash
SERP_API_PROVIDER=yandex          # prod CIS; use duckduckgo for local dev
MAX_CONCURRENT_DOMAINS=12
SEARCH_RESULTS_PER_KEYWORD=5
MAX_PAGES_PER_DOMAIN=3
HTTP_FETCH_ENABLED=true
USE_YANDEXGPT=true
YANDEX_IAM_TOKEN=...
YANDEX_FOLDER_ID=...
```

Full template: `.env.example`. Production SERP: [YANDEX_SEARCH_SETUP.md](YANDEX_SEARCH_SETUP.md).

---

## Monitoring

```bash
python scripts/monitor_workers.py
python scripts/recover_stale_tasks.py
curl http://127.0.0.1:8000/health   # when api_server / healthcheck is running
```

---

## Performance (rough)

- Parallelism: up to `MAX_CONCURRENT_DOMAINS` tasks at once (search/crawl/extract mix)
- One keyword: depends on SERP size, crawl timeouts, LLM — often minutes, not seconds
- Pipeline run: bounded by `_wait_for_completion` timeout and keyword count

---

## Further reading

- [TASK_QUEUE.md](TASK_QUEUE.md) — queue types and dependencies
- [KEYWORDS_GUIDE.md](KEYWORDS_GUIDE.md) — keywords (incl. translation API not wired on add)
- [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) — short architecture index
