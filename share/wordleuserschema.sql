-- $ sqlite3 ./var/wordleUser.db < ./share/wordleuserschema.sql

PRAGMA foreign_keys=ON;
BEGIN TRANSACTION;

DROP TABLE IF EXISTS User;
CREATE TABLE User(user_id INTEGER PRIMARY KEY, username VARCHAR, password VARCHAR,UNIQUE(username));

INSERT INTO User(username, password) VALUES ("Arati", "pass123");
INSERT INTO User(username, password) VALUES ("Dillon", "pass456");
INSERT INTO User(username, password) VALUES ("Brijesh", "pass789");
INSERT INTO User(username, password) VALUES ("Sreevidya", "pass980");

COMMIT;