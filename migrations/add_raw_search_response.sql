-- Migration to add raw_search_response field
USE kalmyk3j_contact;

-- Add raw_search_response column to search_results
ALTER TABLE search_results 
ADD COLUMN raw_search_response JSON AFTER raw_search_query;

-- Verify change
SHOW COLUMNS FROM search_results LIKE 'raw_search_response';

SELECT 'Migration completed successfully!' AS status;
