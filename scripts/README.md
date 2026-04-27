# Scripts Directory

Utility scripts for the B2B Contact Miner project.

## How to Run

All scripts should be run from the **project root** directory:

```bash
cd c:\Users\romanov\PycharmProjects\b2b-contact-miner
python scripts/script_name.py
```

Or use relative imports if running from scripts directory:

```bash
cd scripts
python script_name.py
```

## Available Scripts

### Data Export
- `export_flat.py` - Export contacts to flat CSV format
- `export_for_llm_test.py` - Export data for LLM testing

### Database Checks
- `check_contacts.py` - Analyze contacts in database
- `check_new_records.py` - Check for new records
- `recover_stale_tasks.py` - Recover stuck tasks

### Monitoring
- `monitor_workers.py` - Monitor worker processes and task queue

### Automation
- `register_weekly_smoke_task.ps1` - Register a Windows Task Scheduler job for weekly smoke KPI checks
  ```powershell
  # Default: every Sunday at 03:00
  powershell -ExecutionPolicy Bypass -File scripts/register_weekly_smoke_task.ps1

  # Custom thresholds and time
  powershell -ExecutionPolicy Bypass -File scripts/register_weekly_smoke_task.ps1 `
    -Day MON -Time 02:30 -Limit 15 `
    -MinWithContactsRate 25 -MaxZeroPageRate 45 -MaxFailures 0
  ```

### Testing & Validation
- `validate_setup.py` - Validate project setup and dependencies
- `test_async_pipeline.py` - Test async pipeline functionality
- `test_yandex_token.py` - Test Yandex token authentication

### Token Management
- `exchange_oauth_token.py` - Exchange OAuth tokens
- `refresh_yandex_token.py` - Refresh Yandex IAM tokens

### Utilities
- `download_sonar_report.py` - Download SonarCloud analysis reports
- `scheduler.py` - Task scheduler

## Note

All scripts automatically add the project root to Python path, so you can import modules like:
```python
from models.database import SessionLocal
from services.extraction_service import ExtractionService
```
