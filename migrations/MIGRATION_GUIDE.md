# Migration Guide: Redis to Database Task Queue

## Overview
This migration replaces Redis-based task queue with MySQL database-backed queue for better reliability and persistence.

## Benefits
- ✅ **Persistent storage** - Tasks survive server restarts
- ✅ **No external dependencies** - No need for Redis server
- ✅ **Better monitoring** - Full visibility into task history
- ✅ **Easier backup** - Tasks backed up with database
- ✅ **Retry logic** - Built-in retry mechanism with tracking

## Trade-offs
- ⚠️ **Slower** - Database operations are slower than Redis (but acceptable for our use case)
- ⚠️ **More DB load** - Additional queries for task management

## Migration Steps

### 1. Apply Database Migration
```bash
cd c:\Users\romanov\PycharmProjects\b2b-contact-miner
python migrations/apply_migrations.py
```

This will create the `task_queue` table in your MySQL database.

### 2. Update Code References
The following files have been updated:
- ✅ `models/task_queue.py` - New model for task queue
- ✅ `models/__init__.py` - Export TaskQueue model
- ✅ `workers/db_task_queue.py` - New database-backed task queue implementation
- ✅ `monitoring/healthcheck.py` - Updated to use DB queue
- ✅ `migrations/add_task_queue_table.sql` - SQL migration script
- ✅ `migrations/apply_migrations.py` - Migration runner

### 3. Update main.py
Replace AsyncTaskQueue with DatabaseTaskQueue in your main pipeline:

```python
# OLD CODE:
from workers.task_worker import AsyncTaskQueue
task_queue = AsyncTaskQueue(max_concurrent=20)

# NEW CODE:
from workers.db_task_queue import DatabaseTaskQueue
task_queue = DatabaseTaskQueue(max_concurrent=20)
```

### 4. Update Task Submission
When submitting tasks, use the new API:

```python
# OLD CODE (in-memory):
await task_queue.add_task(crawl_function, domain, keyword_id)

# NEW CODE (database-backed):
task_id = await task_queue.add_task(
    task_name=f"Crawl {domain}",
    task_type='crawl_domain',
    payload={'domain': domain, 'keyword_id': keyword_id},
    priority=0,
    max_retries=3
)
```

### 5. Restart Services
```powershell
.\start_all.ps1 restart
```

### 6. Verify Migration
Check health endpoint:
```bash
curl http://localhost:8000/health
```

You should see:
```json
{
  "status": "healthy",
  "services": {
    "database": {"status": "healthy"},
    "task_queue": {
      "status": "healthy",
      "type": "database",
      "pending_tasks": 0,
      ...
    }
  }
}
```

## Rollback Plan
If you need to rollback:
1. Revert code changes
2. Drop the task_queue table: `DROP TABLE task_queue;`
3. Restart services

## Monitoring
New endpoints for task queue monitoring:
- `GET /api/queue/stats` - Queue statistics
- `POST /api/queue/clear` - Clear old completed tasks

## FAQ

**Q: Will existing tasks be lost?**
A: If you're currently using in-memory queue, yes. But that's expected - in-memory queues don't persist anyway.

**Q: How much slower is it?**
A: Database operations add ~50-100ms per task operation vs ~1ms for Redis. For our use case (minutes-long crawling tasks), this is negligible.

**Q: Can I still use Redis later?**
A: Yes! The architecture allows switching back. Just implement a RedisTaskQueue class with the same interface.

**Q: What happens on database connection failure?**
A: Tasks will fail gracefully with error logging. The system will retry when DB is available again.
