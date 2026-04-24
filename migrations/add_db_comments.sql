-- Add column comments to existing database tables
-- Run this script to add documentation to MySQL database
-- Usage: mysql -u username -p database_name < add_db_comments.sql

-- Disable foreign key checks temporarily
SET FOREIGN_KEY_CHECKS = 0;

-- Keywords table
ALTER TABLE `keywords` 
    MODIFY COLUMN `id` INT COMMENT 'Unique identifier',
    MODIFY COLUMN `keyword` VARCHAR(500) COMMENT 'Search query text',
    MODIFY COLUMN `language` VARCHAR(10) COMMENT 'Language code (ru, en, etc.)',
    MODIFY COLUMN `country` VARCHAR(5) COMMENT 'Country code (RU, US, etc.)',
    MODIFY COLUMN `is_processed` BOOLEAN COMMENT 'True if keyword has been fully processed',
    MODIFY COLUMN `last_crawled_at` DATETIME COMMENT 'Timestamp of last crawl operation',
    MODIFY COLUMN `created_at` DATETIME COMMENT 'Record creation timestamp',
    MODIFY COLUMN `updated_at` DATETIME COMMENT 'Last update timestamp';

-- Search results table
ALTER TABLE `search_results` 
    MODIFY COLUMN `id` INT COMMENT 'Unique identifier',
    MODIFY COLUMN `keyword_id` INT COMMENT 'Foreign key to keywords table',
    MODIFY COLUMN `url` VARCHAR(768) COMMENT 'Website URL from search results',
    MODIFY COLUMN `title` VARCHAR(1000) COMMENT 'Page title from SERP',
    MODIFY COLUMN `snippet` TEXT COMMENT 'Text snippet/description from SERP',
    MODIFY COLUMN `position` INT COMMENT 'Position in search results (1, 2, 3, ...)',
    MODIFY COLUMN `is_processed` BOOLEAN COMMENT 'True if URL has been crawled',
    MODIFY COLUMN `raw_search_query` TEXT COMMENT 'Raw query sent to SERP provider',
    MODIFY COLUMN `raw_search_response` JSON COMMENT 'Raw JSON response from SERP provider',
    MODIFY COLUMN `created_at` DATETIME COMMENT 'Record creation timestamp';

-- Domain contacts table
ALTER TABLE `domain_contacts` 
    MODIFY COLUMN `id` INT COMMENT 'Unique identifier',
    MODIFY COLUMN `search_result_id` INT COMMENT 'Foreign key to search_results table',
    MODIFY COLUMN `domain` VARCHAR(500) COMMENT 'Domain name (e.g., example.com)',
    MODIFY COLUMN `tags` JSON COMMENT 'Tags/categories extracted from website',
    MODIFY COLUMN `metadata` JSON COMMENT 'Website metadata (title, description, etc.)',
    MODIFY COLUMN `contacts_json` JSON COMMENT 'Hybrid: JSON for fast read {emails, telegram, linkedin, phones}',
    MODIFY COLUMN `extraction_method` VARCHAR(50) COMMENT 'Method used: llm, regex, html_parse',
    MODIFY COLUMN `confidence_score` INT COMMENT 'Confidence score 0-100',
    MODIFY COLUMN `is_verified` BOOLEAN COMMENT 'True if contacts have been verified',
    MODIFY COLUMN `created_at` DATETIME COMMENT 'Record creation timestamp',
    MODIFY COLUMN `updated_at` DATETIME COMMENT 'Last update timestamp';

-- Contacts table
ALTER TABLE `contacts` 
    MODIFY COLUMN `id` INT COMMENT 'Unique identifier',
    MODIFY COLUMN `domain_contact_id` INT COMMENT 'Foreign key to domain_contacts table',
    MODIFY COLUMN `contact_type` ENUM('email','telegram','linkedin','phone') COMMENT 'Type: email, telegram, linkedin, phone',
    MODIFY COLUMN `value` VARCHAR(500) COMMENT 'Contact value (email address, phone number, etc.)',
    MODIFY COLUMN `is_verified` BOOLEAN COMMENT 'True if contact has been verified',
    MODIFY COLUMN `verification_date` DATETIME COMMENT 'Date of last verification',
    MODIFY COLUMN `created_at` DATETIME COMMENT 'Record creation timestamp';

-- Crawl logs table
ALTER TABLE `crawl_logs` 
    MODIFY COLUMN `id` INT COMMENT 'Unique identifier',
    MODIFY COLUMN `domain` VARCHAR(500) COMMENT 'Domain that was crawled',
    MODIFY COLUMN `url` VARCHAR(2000) COMMENT 'Specific URL crawled',
    MODIFY COLUMN `status_code` INT COMMENT 'HTTP status code (200, 404, 500, etc.)',
    MODIFY COLUMN `error_message` TEXT COMMENT 'Error message if crawl failed',
    MODIFY COLUMN `pages_crawled` INT COMMENT 'Number of pages crawled on this domain',
    MODIFY COLUMN `duration_seconds` INT COMMENT 'Crawl duration in seconds',
    MODIFY COLUMN `llm_request` TEXT COMMENT 'Raw request sent to LLM',
    MODIFY COLUMN `llm_response` TEXT COMMENT 'Raw response from LLM',
    MODIFY COLUMN `llm_model` VARCHAR(100) COMMENT 'LLM model used (e.g., yandexgpt, deepseek, openai)',
    MODIFY COLUMN `crawled_at` DATETIME COMMENT 'Crawl timestamp';

-- Pipeline state table
ALTER TABLE `pipeline_state` 
    MODIFY COLUMN `id` INT COMMENT 'Unique identifier',
    MODIFY COLUMN `run_id` VARCHAR(100) COMMENT 'Unique pipeline run identifier',
    MODIFY COLUMN `keyword_id` INT COMMENT 'Current keyword being processed',
    MODIFY COLUMN `status` VARCHAR(50) COMMENT 'Status: pending, running, completed, failed',
    MODIFY COLUMN `progress_percent` INT COMMENT 'Progress percentage 0-100',
    MODIFY COLUMN `websites_processed` INT COMMENT 'Number of websites processed',
    MODIFY COLUMN `contacts_found` INT COMMENT 'Total contacts found in this run',
    MODIFY COLUMN `started_at` DATETIME COMMENT 'Pipeline start timestamp',
    MODIFY COLUMN `updated_at` DATETIME COMMENT 'Last update timestamp',
    MODIFY COLUMN `error_message` TEXT COMMENT 'Error message if pipeline failed';

-- Task queue table
ALTER TABLE `task_queue` 
    MODIFY COLUMN `id` INT COMMENT 'Unique task identifier',
    MODIFY COLUMN `task_name` VARCHAR(255) COMMENT 'Human-readable task name',
    MODIFY COLUMN `task_type` VARCHAR(100) COMMENT 'Task type: search_keyword, crawl_domain, extract_contacts, save_results',
    MODIFY COLUMN `payload` TEXT COMMENT 'JSON serialized task data/parameters',
    MODIFY COLUMN `status` VARCHAR(50) COMMENT 'Status: pending, running, completed, failed, retrying',
    MODIFY COLUMN `priority` INT COMMENT 'Priority level (higher number = higher priority)',
    MODIFY COLUMN `retry_count` INT COMMENT 'Current retry attempt count',
    MODIFY COLUMN `max_retries` INT COMMENT 'Maximum retry attempts allowed',
    MODIFY COLUMN `error_message` TEXT COMMENT 'Error message if task failed',
    MODIFY COLUMN `result` TEXT COMMENT 'JSON serialized task result/output',
    MODIFY COLUMN `keyword_id` INT COMMENT 'Associated keyword ID for tracking',
    MODIFY COLUMN `depends_on_task_id` INT COMMENT 'Parent task ID - this task waits for parent completion',
    MODIFY COLUMN `created_at` DATETIME COMMENT 'Task creation timestamp',
    MODIFY COLUMN `started_at` DATETIME COMMENT 'Task execution start timestamp',
    MODIFY COLUMN `completed_at` DATETIME COMMENT 'Task completion timestamp',
    MODIFY COLUMN `scheduled_for` DATETIME COMMENT 'Scheduled execution time for delayed tasks',
    MODIFY COLUMN `locked_by` VARCHAR(100) COMMENT 'Worker ID that locked this task for execution',
    MODIFY COLUMN `locked_at` DATETIME COMMENT 'Task lock timestamp';

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Verify comments were added
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
AND COLUMN_COMMENT != ''
ORDER BY TABLE_NAME, ORDINAL_POSITION;
