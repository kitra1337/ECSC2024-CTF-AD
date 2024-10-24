CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    date TEXT NOT NULL,
    template_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (template_id) REFERENCES templates(id)
);

CREATE TABLE keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    UNIQUE (id, user_id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE secret_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id INTEGER NOT NULL,
    FOREIGN KEY (key_id) REFERENCES keys(id)
);

CREATE TABLE templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT NOT NULL,
    template TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

/* TODO: creare template di default*/
INSERT INTO templates(user_id, name, template) VALUES (NULL, 'Default letter', 'Template body');