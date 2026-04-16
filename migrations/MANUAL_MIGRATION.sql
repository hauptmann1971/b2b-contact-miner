-- Manual migration script for task_queue table
-- Run this directly in your MySQL client if apply_migrations.py fails

USE kalmyk3j_contact;

CREATE TABLE IF NOT EXISTS task_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    payload TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    priority INT DEFAULT 0,
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    error_message TEXT,
    result TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    completed_at DATETIME,
    scheduled_for DATETIME,
    locked_by VARCHAR(100),
    locked_at DATETIME,
    INDEX idx_status (status),
    INDEX idx_task_type (task_type),
    INDEX idx_priority (priority),
    INDEX idx_created_at (created_at),
    INDEX idx_scheduled_for (scheduled_for)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE task_queue COMMENT 'Persistent task queue for background job processing';

-- Verify table was created
SHOW TABLES LIKE 'task_queue';
SELECT 'Migration completed successfully!' AS status;
