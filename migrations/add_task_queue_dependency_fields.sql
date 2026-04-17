-- Migration to add dependency tracking fields to task_queue table
-- Run this if task_queue table already exists

ALTER TABLE task_queue 
ADD COLUMN keyword_id INT NULL,
ADD COLUMN depends_on_task_id INT NULL;

-- Add indexes for better query performance
CREATE INDEX idx_task_queue_keyword_id ON task_queue(keyword_id);
CREATE INDEX idx_task_queue_depends_on ON task_queue(depends_on_task_id);

-- Add foreign key constraint for depends_on_task_id (optional, can be skipped if not needed)
-- ALTER TABLE task_queue 
-- ADD CONSTRAINT fk_task_queue_parent 
-- FOREIGN KEY (depends_on_task_id) REFERENCES task_queue(id) ON DELETE SET NULL;
