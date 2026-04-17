# Async Parallel Pipeline - Migration Guide

## Overview

The B2B Contact Miner pipeline has been upgraded from **sequential processing** to **async parallel processing** using a database-backed task queue.

### What Changed?

**Before (Sequential):**
```
Keyword 1 → Search → Crawl → Extract → Save (2 min)
Keyword 2 → Search → Crawl → Extract → Save (2 min)
Keyword 3 → Search → Crawl → Extract → Save (2 min)
Total: 6 minutes for 3 keywords
```

**After (Parallel):**
```
Workers process tasks from queue concurrently:
- Worker 1: Search Keyword 1
- Worker 2: Search Keyword 2  
- Worker 3: Crawl site1.com (from Keyword 1)
- Worker 4: Crawl site2.com (from Keyword 2)
- Worker 5: Extract contacts from site3.com
...all happening simultaneously!

Total: ~1-2 minutes for 3 keywords (3-6x faster!)
```

---

## Architecture

### Task Types

The pipeline now breaks down work into small, independent tasks:

1. **`search_keyword`** (Priority: 10)
   - Performs SERP search for a keyword
   - Creates `crawl_domain` tasks for each result URL
   - Saves results to `search_results` table

2. **`crawl_domain`** (Priority: 5)
   - Crawls a single domain using Playwright
   - Identifies contact pages
   - Creates `extract_contacts` task
   - Saves metadata to `crawl_logs` table

3. **`extract_contacts`** (Priority: 7)
   - Crawls contact pages (fast mode)
   - Extracts emails, Telegram, LinkedIn using regex + LLM
   - Verifies emails via MX records
   - Saves final results to `domain_contacts` and `contacts` tables

### Task Dependencies

Tasks use a **chain pattern** - each task creates the next tasks upon completion:

```
search_keyword (task #1)
  ↓ creates
crawl_domain (tasks #2-6) - one per search result
  ↓ each creates
extract_contacts (tasks #7-11) - one per crawled domain
  ↓ saves directly to DB
Final contacts saved!
```

Dependencies are tracked via `depends_on_task_id` field in `task_queue` table.

---

## Database Changes

### New Fields in `task_queue` Table

```sql
ALTER TABLE task_queue 
ADD COLUMN keyword_id INT NULL,              -- Link task to keyword
ADD COLUMN depends_on_task_id INT NULL;      -- Parent task dependency

CREATE INDEX idx_task_queue_keyword_id ON task_queue(keyword_id);
CREATE INDEX idx_task_queue_depends_on ON task_queue(depends_on_task_id);
```

**Apply migration:**
```bash
python migrations/apply_task_queue_dependency_migration.py
```

---

## Configuration

New settings in `.env` or `config/settings.py`:

```python
# Task Queue Retry Settings
SEARCH_MAX_RETRIES = 3      # SERP API может fail
CRAWL_MAX_RETRIES = 2       # Сайт может быть down
EXTRACT_MAX_RETRIES = 1     # LLM может timeout
SAVE_MAX_RETRIES = 3        # DB lock issues
TASK_LOCK_TIMEOUT = 300     # seconds before lock expires (5 minutes)
```

---

## Usage

### Running the Pipeline

**Same command as before:**
```bash
python main.py
```

But now it runs in **async parallel mode**:
1. Adds all pending keywords as search tasks to queue
2. Workers automatically pick up and process tasks
3. Monitors progress until all tasks complete
4. Shows real-time queue statistics

### Monitoring Progress

**Check queue stats via API:**
```bash
curl http://localhost:8000/metrics/pipeline
```

Response:
```json
{
  "pipeline": {...},
  "queue": {
    "pending": 15,
    "running": 5,
    "completed": 30,
    "failed": 2,
    "total": 52,
    "current_workers": 5,
    "keywords_in_progress": 3
  },
  "timestamp": "2026-04-17T10:30:00"
}
```

**Via web UI:**
- Visit `http://localhost:5000/health-check`
- Real-time queue visualization

---

## Key Features

### 1. **Automatic Stale Task Recovery**

If workers crash or pipeline is interrupted:
- Tasks stuck in 'running' state for >5 minutes are automatically reset to 'pending'
- Recovery happens on next pipeline start
- No manual intervention needed

### 2. **Graceful Shutdown**

Press `Ctrl+C` to stop:
- Workers finish current tasks
- New tasks are not accepted
- Queue state is preserved
- Resume on next run

### 3. **Per-Domain Results**

Each domain gets its own record in `domain_contacts`:
```python
{
  "id": 1,
  "domain": "site1.com",
  "contacts_json": {
    "emails": ["contact@site1.com"],
    "telegram": ["https://t.me/site1"],
    "linkedin": [],
    "phones": []
  },
  "confidence_score": 75,
  "extraction_method": "llm"
}
```

Normalized `contacts` table for efficient searching:
```python
[
  {"id": 1, "domain_contact_id": 1, "type": "email", "value": "contact@site1.com"},
  {"id": 2, "domain_contact_id": 1, "type": "telegram", "value": "https://t.me/site1"}
]
```

### 4. **Retry Logic**

Different retry counts per task type:
- Search: 3 retries (API failures)
- Crawl: 2 retries (site downtime)
- Extract: 1 retry (LLM timeout)

Failed tasks after max retries are marked as 'failed' but don't block other tasks.

---

## Performance Comparison

### Sequential Mode (Old)
- 10 keywords × 2 URLs each = 20 domains
- Each domain takes ~2 minutes
- **Total: ~40 minutes**

### Parallel Mode (New)
- 20 concurrent workers
- Same 20 domains processed in parallel batches
- **Total: ~4-6 minutes** (6-10x faster!)

---

## Troubleshooting

### Tasks Not Processing

**Check if workers are running:**
```python
# In Python console
from workers.db_task_queue import DatabaseTaskQueue
import asyncio

async def check():
    queue = DatabaseTaskQueue()
    stats = await queue.get_queue_stats()
    print(stats)

asyncio.run(check())
```

**Expected output:**
```python
{
  'pending': 10,
  'running': 5,  # Should match MAX_CONCURRENT_DOMAINS
  'completed': 20,
  'failed': 1,
  'total': 36,
  'current_workers': 5,
  'keywords_in_progress': 3
}
```

### Stale Tasks

**Manually recover stale tasks:**
```bash
python -c "
import asyncio
from workers.db_task_queue import DatabaseTaskQueue

async def recover():
    queue = DatabaseTaskQueue()
    recovered = await queue.recover_stale_tasks()
    print(f'Recovered {recovered} stale tasks')

asyncio.run(recover())
"
```

### Clear Old Tasks

**Remove completed/failed tasks older than 7 days:**
```bash
python -c "
import asyncio
from workers.db_task_queue import DatabaseTaskQueue

async def clear():
    queue = DatabaseTaskQueue()
    deleted = await queue.clear_completed_tasks(older_than_days=7)
    print(f'Deleted {deleted} old tasks')

asyncio.run(clear())
"
```

---

## Migration Steps

1. **Apply database migration:**
   ```bash
   python migrations/apply_task_queue_dependency_migration.py
   ```

2. **Update .env with new settings** (optional, defaults are fine):
   ```bash
   SEARCH_MAX_RETRIES=3
   CRAWL_MAX_RETRIES=2
   EXTRACT_MAX_RETRIES=1
   SAVE_MAX_RETRIES=3
   TASK_LOCK_TIMEOUT=300
   ```

3. **Restart all services:**
   ```bash
   ./start_all.sh restart
   # or
   start_all.bat restart
   ```

4. **Run pipeline:**
   ```bash
   python main.py
   ```

5. **Monitor progress:**
   - Check logs for queue statistics
   - Visit http://localhost:8000/metrics/pipeline
   - Or http://localhost:5000/health-check

---

## Backward Compatibility

✅ **Fully backward compatible!**

- Existing keywords with `is_processed=False` will be processed
- Old data in `search_results`, `domain_contacts`, `contacts` is preserved
- Web UI works without changes
- Scheduler works without changes
- API endpoints unchanged

---

## Future Enhancements

Potential improvements:
- [ ] Dynamic worker scaling based on queue size
- [ ] Task priority boost for high-value keywords
- [ ] Distributed workers across multiple machines
- [ ] WebSocket real-time progress updates
- [ ] Task execution time analytics
- [ ] Automatic retry scheduling for failed tasks

---

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review queue stats at `/metrics/pipeline`
3. Inspect task_queue table for stuck tasks
4. Check health endpoint at `/health`

---

**Enjoy the speed boost! 🚀**
