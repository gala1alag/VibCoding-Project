import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "devhub.db")

def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    try:
        conn.cursor().executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL,
                path            TEXT NOT NULL,
                type            TEXT NOT NULL CHECK(type IN ('folder', 'file')),
                language        TEXT,
                note            TEXT,
                content         TEXT,
                default_editor  TEXT,
                created_at      TEXT DEFAULT (datetime('now', 'localtime')),
                last_opened_at  TEXT
            );

            CREATE TABLE IF NOT EXISTS snippets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                language    TEXT,
                code        TEXT,
                description TEXT,
                project_id  INTEGER REFERENCES projects(id) ON DELETE SET NULL,
                created_at  TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS todos (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id  INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                title       TEXT NOT NULL,
                description TEXT,
                status      TEXT DEFAULT 'todo' CHECK(status IN ('todo', 'doing', 'done')),
                priority    TEXT DEFAULT 'medium' CHECK(priority IN ('high', 'medium', 'low')),
                due_date    TEXT,
                created_at  TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS study_logs (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id       INTEGER REFERENCES projects(id) ON DELETE SET NULL,
                duration_minutes INTEGER NOT NULL,
                date             TEXT NOT NULL,
                created_at       TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS tags (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                name  TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#4A90D9'
            );

            CREATE TABLE IF NOT EXISTS note_tags (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                tag_id     INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
                UNIQUE(project_id, tag_id)
            );

            CREATE TABLE IF NOT EXISTS app_index (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL,
                path            TEXT NOT NULL,
                last_scanned_at TEXT DEFAULT (datetime('now', 'localtime'))
            );
        """)
        cur = conn.cursor()
        for col, definition in [
            ("color", "TEXT DEFAULT '#4A90D9'"),
            ("memo",  "TEXT DEFAULT ''"),
        ]:
            try:
                cur.execute(f"ALTER TABLE projects ADD COLUMN {col} {definition}")
                conn.commit()
            except Exception:
                pass
    finally:
        conn.close()
