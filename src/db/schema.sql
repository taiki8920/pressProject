-- SQLite schema for Press Project

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS persons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    wikipedia_summary TEXT,
    metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    type TEXT,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    title TEXT,
    content TEXT,
    source_id INTEGER,
    published_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(person_id) REFERENCES persons(id) ON DELETE CASCADE,
    FOREIGN KEY(source_id) REFERENCES sources(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER,
    title TEXT,
    markdown TEXT,
    html TEXT,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(person_id) REFERENCES persons(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER,
    snapshot_date DATE,
    diff TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(person_id) REFERENCES persons(id) ON DELETE CASCADE
);

-- LLM / activity logs: store prompts and responses from external LLMs (OpenAI)
CREATE TABLE IF NOT EXISTS llm_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL, -- e.g. 'x_summary', 'article_generation'
    person_id INTEGER,
    url TEXT,
    prompt TEXT,
    response TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(person_id) REFERENCES persons(id) ON DELETE SET NULL
);
