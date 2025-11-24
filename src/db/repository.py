"""Simple SQLite repository for Press Project.

This module provides minimal helpers: init_db, upsert_person, insert_source, insert_activity.
"""
import sqlite3
import json
from typing import Optional, Dict, Any
from pathlib import Path

DB_PATH = Path("data") / "database.sqlite3"


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(schema_path: str = "src/db/schema.sql") -> None:
    """Initialize the SQLite DB using the schema file."""
    schema_file = Path(schema_path)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    conn = get_conn()
    with schema_file.open("r", encoding="utf-8") as f:
        sql = f.read()
    conn.executescript(sql)
    conn.commit()
    conn.close()


def upsert_person(name: str, wikipedia_summary: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM persons WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        person_id = row["id"]
        cur.execute(
            "UPDATE persons SET wikipedia_summary=?, metadata=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (wikipedia_summary, json.dumps(metadata or {}), person_id),
        )
    else:
        cur.execute(
            "INSERT INTO persons (name, wikipedia_summary, metadata) VALUES (?, ?, ?)",
            (name, wikipedia_summary, json.dumps(metadata or {})),
        )
        person_id = cur.lastrowid
    conn.commit()
    conn.close()
    return person_id


def insert_source(url: str, type_: Optional[str] = None) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO sources (url, type) VALUES (?, ?)", (url, type_))
    conn.commit()
    cur.execute("SELECT id FROM sources WHERE url = ?", (url,))
    row = cur.fetchone()
    conn.close()
    return row["id"] if row else -1


def insert_activity(person_id: int, title: str, content: str, source_id: Optional[int] = None, published_at: Optional[str] = None) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO activities (person_id, title, content, source_id, published_at) VALUES (?, ?, ?, ?, ?)",
        (person_id, title, content, source_id, published_at),
    )
    activity_id = cur.lastrowid
    conn.commit()
    conn.close()
    return activity_id


def insert_llm_log(person_id: Optional[int], source: str, url: Optional[str], prompt: Optional[str], response: Optional[str]) -> int:
    """Insert an LLM log row. Returns inserted id or -1 on failure."""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO llm_logs (source, person_id, url, prompt, response) VALUES (?, ?, ?, ?, ?)",
            (source, person_id, url, prompt, response),
        )
        lid = cur.lastrowid
        conn.commit()
        conn.close()
        return lid
    except Exception:
        # Do not let logging break main flows
        try:
            conn.close()
        except Exception:
            pass
        return -1
