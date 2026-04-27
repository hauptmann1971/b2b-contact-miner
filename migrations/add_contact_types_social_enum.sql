-- Migration: extend contacts.contact_type ENUM with social platforms
USE kalmyk3j_contact;

ALTER TABLE `contacts`
    MODIFY COLUMN `contact_type`
    ENUM('email','telegram','linkedin','phone','x','facebook','instagram','youtube')
    COMMENT 'Type: email, telegram, linkedin, phone, x, facebook, instagram, youtube';

-- Verify ENUM values
SHOW COLUMNS FROM `contacts` LIKE 'contact_type';

SELECT 'Migration completed successfully!' AS status;
