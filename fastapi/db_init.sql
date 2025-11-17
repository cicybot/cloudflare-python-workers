-- DROP TABLE IF EXISTS users;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password Text
);

INSERT INTO users (username, password)
SELECT * FROM (
    VALUES
        ("tom", "password1"),
        ("jack", "password1")
) WHERE NOT EXISTS (SELECT 1 FROM users);
