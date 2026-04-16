-- Migration to add contacts_json for hybrid approach
USE kalmyk3j_contact;

-- Add contacts_json column to domain_contacts
ALTER TABLE domain_contacts 
ADD COLUMN IF NOT EXISTS contacts_json JSON AFTER site_metadata;

-- Verify change
SHOW COLUMNS FROM domain_contacts LIKE 'contacts_json';

SELECT 'Migration completed successfully!' AS status;
