# Database Schema Documentation

## Overview

This document describes the database schema for B2B Contact Miner with detailed field descriptions.

**Multi-tenant:** each company (`tenants`) has isolated data via `tenant_id` on business tables. Users authenticate against `users`. See [AUTH_MULTITENANT.md](AUTH_MULTITENANT.md).

## Tables

### 0. `tenants` — Organizations

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Unique identifier |
| `slug` | VARCHAR(64) | Unique slug (e.g. `company`) |
| `name` | VARCHAR(255) | Display name |
| `is_active` | BOOLEAN | Tenant enabled |
| `settings_json` | TEXT | Optional JSON settings |
| `created_at` | DATETIME | Created |
| `updated_at` | DATETIME | Updated |

---

### 0b. `users` — Login accounts

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Unique identifier |
| `tenant_id` | INT | FK → `tenants.id` |
| `username` | VARCHAR(128) | Login (unique per tenant) |
| `password_hash` | VARCHAR(255) | Werkzeug hash (nullable for Telegram-only) |
| `telegram_id` | INT | Telegram user id (unique, nullable) |
| `display_name` | VARCHAR(255) | UI label |
| `role` | ENUM | `viewer`, `member`, `owner`, `super_admin` |
| `is_active` | BOOLEAN | Account enabled |
| `last_login_at` | DATETIME | Last successful login |
| `created_at` | DATETIME | Created |
| `updated_at` | DATETIME | Updated |

---

### 1. `keywords` - Search Keywords

Stores search queries to process (e.g., "IT companies Moscow").

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Unique identifier |
| `tenant_id` | INT | FK → `tenants.id` (owning company) |
| `created_by_user_id` | INT | FK → `users.id` (who added keyword) |
| `keyword` | VARCHAR(500) | Search query text |
| `language` | VARCHAR(10) | Language code (ru, en, etc.) |
| `country` | VARCHAR(5) | Country code (RU, US, etc.) |
| `is_processed` | BOOLEAN | True if keyword has been fully processed |
| `last_crawled_at` | DATETIME | Timestamp of last crawl operation |
| `created_at` | DATETIME | Record creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes:**
- PRIMARY KEY (`id`)
- UNIQUE (`tenant_id`, `keyword`, `language`, `country`)
- INDEX (`tenant_id`)

---

### 2. `search_results` - SERP Search Results

Stores search engine results pages (SERP) for each keyword.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Unique identifier |
| `tenant_id` | INT | FK → `tenants.id` |
| `keyword_id` | INT | Foreign key to keywords table |
| `url` | VARCHAR(768) | Website URL from search results |
| `title` | VARCHAR(1000) | Page title from SERP |
| `snippet` | TEXT | Text snippet/description from SERP |
| `position` | INT | Position in search results (1, 2, 3, ...) |
| `is_processed` | BOOLEAN | True if URL has been crawled |
| `raw_search_query` | TEXT | Raw query sent to SERP provider |
| `raw_search_response` | JSON | Raw JSON response from SERP provider |
| `created_at` | DATETIME | Record creation timestamp |

**Indexes:**
- PRIMARY KEY (`id`)
- FOREIGN KEY (`keyword_id`) → `keywords.id`
- INDEX (`url`)
- UNIQUE INDEX (`keyword_id`, `url(255)`)

---

### 3. `domain_contacts` - Aggregated Domain Information

Aggregated contact information and metadata for each domain.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Unique identifier |
| `tenant_id` | INT | FK → `tenants.id` |
| `search_result_id` | INT | Foreign key to search_results table |
| `domain` | VARCHAR(500) | Domain name (e.g., example.com) |
| `tags` | JSON | Tags/categories extracted from website |
| `metadata` | JSON | Website metadata (title, description, etc.) |
| `contacts_json` | JSON | Hybrid: JSON for fast read {emails, telegram, linkedin, phones} |
| `extraction_method` | VARCHAR(50) | Method used: llm, regex, html_parse |
| `confidence_score` | INT | Confidence score 0-100 |
| `is_verified` | BOOLEAN | True if contacts have been verified |
| `created_at` | DATETIME | Record creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes:**
- PRIMARY KEY (`id`)
- FOREIGN KEY (`search_result_id`) → `search_results.id`
- INDEX (`domain`)

**Relationships:**
- Has many `contacts` (one-to-many)

---

### 4. `contacts` - Individual Contact Records

Normalized individual contact records for efficient searching.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Unique identifier |
| `tenant_id` | INT | FK → `tenants.id` |
| `domain_contact_id` | INT | Foreign key to domain_contacts table |
| `contact_type` | ENUM | Type: email, telegram, linkedin, phone |
| `value` | VARCHAR(500) | Contact value (email address, phone number, etc.) |
| `is_verified` | BOOLEAN | True if contact has been verified |
| `verification_date` | DATETIME | Date of last verification |
| `created_at` | DATETIME | Record creation timestamp |

**Indexes:**
- PRIMARY KEY (`id`)
- FOREIGN KEY (`domain_contact_id`) → `domain_contacts.id`
- INDEX (`value`)
- INDEX (`contact_type`, `value`)
- INDEX (`domain_contact_id`, `contact_type`)

**Contact Types:**
- `email` - Email addresses
- `telegram` - Telegram usernames/links
- `linkedin` - LinkedIn profiles
- `phone` - Phone numbers

---

### 5. `crawl_logs` - Website Crawling Logs

Logs of all website crawling operations for debugging and monitoring.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Unique identifier |
| `tenant_id` | INT | FK → `tenants.id` (optional) |
| `domain` | VARCHAR(500) | Domain that was crawled |
| `url` | VARCHAR(2000) | Specific URL crawled |
| `status_code` | INT | HTTP status code (200, 404, 500, etc.) |
| `error_message` | TEXT | Error message if crawl failed |
| `pages_crawled` | INT | Number of pages crawled on this domain |
| `duration_seconds` | INT | Crawl duration in seconds |
| `llm_request` | TEXT | Raw request sent to LLM |
| `llm_response` | TEXT | Raw response from LLM |
| `llm_model` | VARCHAR(100) | LLM model used (e.g., yandexgpt, gigachat) |
| `crawled_at` | DATETIME | Crawl timestamp |

**Indexes:**
- PRIMARY KEY (`id`)
- INDEX (`domain`)

---

### 6. `pipeline_state` - Pipeline Progress Tracking

Tracks the state and progress of pipeline runs.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Unique identifier |
| `tenant_id` | INT | FK → `tenants.id` (optional) |
| `run_id` | VARCHAR(100) | Pipeline run identifier (shared across checkpoint rows for the same run) |
| `keyword_id` | INT | Current keyword being processed |
| `status` | VARCHAR(50) | Status: pending, running, completed, failed |
| `progress_percent` | INT | Progress percentage 0-100 |
| `websites_processed` | INT | Number of websites processed |
| `contacts_found` | INT | Total contacts found in this run |
| `started_at` | DATETIME | Pipeline start timestamp |
| `updated_at` | DATETIME | Last update timestamp |
| `error_message` | TEXT | Error message if pipeline failed |

**Indexes:**
- PRIMARY KEY (`id`)
- FOREIGN KEY (`keyword_id`) → `keywords.id`
- INDEX (`run_id`) — non-unique (multiple rows per run)

**Status Values:**
- `pending` - Not started yet
- `running` - Currently processing
- `completed` - Finished successfully
- `failed` - Failed with error

---

### 7. `task_queue` - Persistent Task Queue

Persistent task queue for reliable asynchronous processing.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Unique task identifier |
| `task_name` | VARCHAR(255) | Human-readable task name |
| `task_type` | VARCHAR(100) | Task type: search_keyword, crawl_domain, extract_contacts (save_results in code comments only; no handler) |
| `payload` | TEXT | JSON serialized task data/parameters |
| `status` | VARCHAR(50) | Status: pending, running, completed, failed, retrying |
| `priority` | INT | Priority level (higher number = higher priority) |
| `retry_count` | INT | Current retry attempt count |
| `max_retries` | INT | Maximum retry attempts allowed |
| `error_message` | TEXT | Error message if task failed |
| `result` | TEXT | JSON serialized task result/output |
| `keyword_id` | INT | Associated keyword ID for tracking |
| `tenant_id` | INT | FK → `tenants.id` (optional) |
| `depends_on_task_id` | INT | Parent task ID - this task waits for parent completion |
| `created_at` | DATETIME | Task creation timestamp |
| `started_at` | DATETIME | Task execution start timestamp |
| `completed_at` | DATETIME | Task completion timestamp |
| `scheduled_for` | DATETIME | Scheduled execution time for delayed tasks |
| `locked_by` | VARCHAR(100) | Worker ID that locked this task for execution |
| `locked_at` | DATETIME | Task lock timestamp |

**Indexes:**
- PRIMARY KEY (`id`)
- FOREIGN KEY (`depends_on_task_id`) → `task_queue.id` (self-reference)
- INDEX (`task_name`)
- INDEX (`task_type`)
- INDEX (`status`)
- INDEX (`priority`)
- INDEX (`keyword_id`)
- INDEX (`depends_on_task_id`)
- INDEX (`created_at`)
- INDEX (`scheduled_for`)

**Task Types:**
- `search_keyword` - Search for keyword in SERP
- `crawl_domain` - Crawl website domain
- `extract_contacts` - Extract contacts (regex / JSON-LD / optional LLM)
- SERP rows are saved inside `search_keyword`, not a separate queue task

**Status Values:**
- `pending` - Waiting to be processed
- `running` - Currently being executed
- `completed` - Finished successfully
- `failed` - Failed after max retries
- `retrying` - Will be retried

---

## Entity Relationships

```
tenants (1) ──────< users (N)

tenants (1) ──────< keywords (N) ──────< search_results (N)
                               │
                               └──> domain_contacts (1) ──────< contacts (N)
                                      │
                                      └──> crawl_logs (logs)

pipeline_state ──> keywords

task_queue ──> keywords (optional), tenant_id
     │
     └──> task_queue (self-reference for dependencies)
```

---

## Viewing Comments in Database Tools

### phpMyAdmin
Comments appear in the "Structure" tab under each column.

### MySQL Workbench
Right-click table → "Table Inspector" → "Columns" tab shows comments.

### DBeaver
Comments shown in column properties panel.

### Command Line
```sql
SHOW FULL COLUMNS FROM keywords;
-- or
SELECT COLUMN_NAME, COLUMN_COMMENT 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'your_database' 
AND TABLE_NAME = 'keywords';
```

---

## Adding Comments to Existing Database

If comments are missing, run the migration script:

```bash
mysql -u username -p database_name < migrations/add_db_comments.sql
```

Or on remote server:
```bash
ssh root@85.198.86.237 "mysql -u user -p'password' -h host database < /tmp/add_db_comments.sql"
```

---

## Best Practices

1. **Always check comments** when adding new columns
2. **Update this documentation** when schema changes
3. **Use meaningful column names** that match their purpose
4. **Add indexes** for frequently queried columns
5. **Monitor foreign key relationships** to avoid constraint issues

---

## Quick Reference Queries

### Check table structure with comments
```sql
SHOW FULL COLUMNS FROM keywords;
```

### Find all tables and their row counts
```sql
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    DATA_LENGTH,
    INDEX_LENGTH
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = DATABASE()
ORDER BY TABLE_NAME;
```

### View task queue statistics
```sql
SELECT 
    task_type,
    status,
    COUNT(*) as count,
    AVG(retry_count) as avg_retries
FROM task_queue
GROUP BY task_type, status
ORDER BY task_type, status;
```

### Find unprocessed keywords
```sql
SELECT * FROM keywords 
WHERE is_processed = FALSE 
ORDER BY created_at DESC;
```
