-- Migration to add LLM tracking fields
USE kalmyk3j_contact;

-- Add raw_search_query to search_results
ALTER TABLE search_results 
ADD COLUMN IF NOT EXISTS raw_search_query TEXT AFTER is_processed;

-- Add LLM fields to crawl_logs
ALTER TABLE crawl_logs 
ADD COLUMN IF NOT EXISTS llm_request TEXT AFTER duration_seconds,
ADD COLUMN IF NOT EXISTS llm_response TEXT AFTER llm_request,
ADD COLUMN IF NOT EXISTS llm_model VARCHAR(100) AFTER llm_response;

-- Verify changes
SHOW COLUMNS FROM search_results LIKE 'raw_search_query';
SHOW COLUMNS FROM crawl_logs LIKE 'llm_%';

SELECT 'Migration completed successfully!' AS status;
