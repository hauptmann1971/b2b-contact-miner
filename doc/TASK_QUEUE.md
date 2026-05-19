# Task queue (current behavior)

The pipeline uses a **MySQL-backed** queue (`task_queue` table), not Redis.

## Components

| File | Role |
|------|------|
| `models/task_queue.py` | SQLAlchemy model |
| `workers/db_task_queue.py` | Workers: lock rows, run handlers, retries |
| `main.py` | Enqueues `search_keyword` tasks, waits for completion |

## Task types (handlers)

| `task_type` | Handler | What it does |
|-------------|---------|----------------|
| `search_keyword` | `_handle_search_task` | SERP search, save `search_results`, enqueue `crawl_domain` / snippet-only `extract_contacts` |
| `crawl_domain` | `_handle_crawl_task` | HTTP-first + Playwright crawl, enqueue `extract_contacts` |
| `extract_contacts` | `_handle_extract_task` | Regex / JSON-LD / LLM, save `domain_contacts` + `contacts` |

`save_results` appears in schema comments and retry maps but **has no separate handler** — SERP results are saved inside `search_keyword`.

## Concurrency

```python
# main.py
DatabaseTaskQueue(max_concurrent=settings.MAX_CONCURRENT_DOMAINS)  # default 12
```

Each worker is an asyncio task polling `task_queue` with row locking (`locked_by`, `locked_at`).

## Dependencies

Child tasks use `depends_on_task_id`:

- `crawl_domain` / `extract_contacts` wait until parent `search_keyword` completes (or fails per rules in `db_task_queue.py`).

## Ops

```bash
python scripts/monitor_workers.py
python scripts/recover_stale_tasks.py
python scripts/unblock_orphan_queue_tasks.py
```

See [scripts/README.md](../scripts/README.md) and [MONITORING_CHEATSHEET.md](MONITORING_CHEATSHEET.md).

## Migration history

One-time migration notes: [DB_TASK_QUEUE_SETUP.md](DB_TASK_QUEUE_SETUP.md) (historical).
