CREATE DATABASE db;

USE db;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INTEGER,
    name VARCHAR(255) NOT NULL,
    template TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);


CREATE TABLE documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    date TEXT NOT NULL,
    template_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (template_id) REFERENCES templates(id)
);

CREATE TABLE user_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE secret_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_id INT NOT NULL,
    FOREIGN KEY (key_id) REFERENCES user_keys (id)
);

CREATE TABLE notifications(
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    body VARCHAR(7500),
    FOREIGN KEY (user_id) REFERENCES users(id)
);


INSERT INTO templates(user_id, name, template) VALUES (NULL, 'Blank Template', '{body}');
