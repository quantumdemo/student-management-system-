CREATE DATABASE IF NOT EXISTS studentdb;
USE studentdb;

CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password_hash TEXT
);

CREATE TABLE student (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    class_level VARCHAR(20),
    student_id VARCHAR(20) UNIQUE,
    password_hash TEXT
);

CREATE TABLE result (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20),
    subject VARCHAR(100),
    score FLOAT
);

INSERT INTO admin (username, password_hash)
VALUES ('admin', '$pbkdf2:sha256:260000$KZhOWGUkL27SS7mO7VjOgX$GMiDhWzCFY2lJtsfKjA3ojzr1mymjkFz5YiPRNcZ2js');
