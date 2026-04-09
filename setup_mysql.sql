-- MySQL Database Setup Script
-- Run this script to create the database and user

-- Create database with UTF-8 support
CREATE DATABASE IF NOT EXISTS contact_miner 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- Create user (change 'your_password' to a secure password)
CREATE USER IF NOT EXISTS 'miner'@'localhost' IDENTIFIED BY 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON contact_miner.* TO 'miner'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;

-- Verify
SELECT 'Database created successfully!' AS status;
USE contact_miner;
SELECT DATABASE() AS current_database;
