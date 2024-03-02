DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS book;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    borrow INTEGER DEFAULT 0
);

CREATE TABLE book (
    ISBN CHAR(13) PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT,
    publisher TEXT,
    stock INTEGER DEFAULT 1
);

CREATE TABLE borrow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    book_ISBN CHAR(13) NOT NULL,
    borrow_date DATE NOT NULL,
    return_date DATE,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (book_ISBN) REFERENCES book(ISBN)
);