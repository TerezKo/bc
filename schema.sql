-- schema.sql

-- Drop the table if it exists (for development purposes)
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS non_prefer;
DROP TABLE IF EXISTS prefer;
DROP TABLE IF EXISTS submissions;

-- Create the users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    max_hours TEXT,
    min_hours TEXT,
    position TEXT,
    is_certified TEXT,
    address TEXT,
    mobile TEXT,
    birthdate DATE,
    workplace TEXT,
    work_at_night TEXT,
    status TEXT
);


CREATE TABLE IF NOT EXISTS non_prefer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    day INTEGER,
    shift_type TEXT,
    reason_strength TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS prefer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    day INTEGER,
    shift_type TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        submission_date TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month_year INTEGER UNIQUE NOT NULL,
        lekari TEXT,
        sestry_JIS TEXT,
        sestry_odd TEXT,
        prak_sestry_JIS TEXT,
        prak_sestry_odd TEXT,
        oset_JIS TEXT,
        oset_odd TEXT
);



