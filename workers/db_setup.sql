-- Create database
CREATE DATABASE IF NOT EXISTS tasks_db;

-- Use database
USE tasks_db;

-- Create tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id VARCHAR(36) PRIMARY KEY,
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    duration FLOAT DEFAULT NULL,
    error_msg TEXT DEFAULT NULL,
    retry_time INT DEFAULT 3,
    task_result JSON DEFAULT NULL,
    task_type VARCHAR(50) DEFAULT NULL
);