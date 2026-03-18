"""
Database connection and schema management for the Productivity Tracker.
Uses SQLite for lightweight, file-based persistence.
"""

import sqlite3
import os
from .config import DB_PATH


from contextlib import contextmanager

def get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    # We turn ON foreign_keys later in the connection, or selectively, since migrations might violate it temporarily.
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

@contextmanager
def db_session():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_db():
    """Create all tables if they don't exist and run migrations."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT '#5B9BD5',
            is_custom INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS subcategories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            is_custom INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
            UNIQUE(category_id, name)
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            project_id INTEGER NOT NULL DEFAULT 1,
            category_id INTEGER,
            subcategory_id INTEGER,
            notes TEXT DEFAULT '',
            status TEXT DEFAULT 'active' CHECK(status IN ('active','paused','break','completed')),
            total_active_seconds REAL DEFAULT 0,
            total_break_seconds REAL DEFAULT 0,
            total_pause_seconds REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (subcategory_id) REFERENCES subcategories(id)
        );

        CREATE TABLE IF NOT EXISTS time_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            event_type TEXT NOT NULL CHECK(event_type IN ('start','pause','resume','break_start','break_end','stop')),
            timestamp TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)

    # Migration: Add default project if none exists, and migrate old sessions if they miss project_id
    # Ensure there is at least one project.
    cursor.execute("SELECT COUNT(*) as count FROM projects")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("INSERT INTO projects (id, name, description) VALUES (1, 'Default Project', 'Default overarching project.')")
    
    # Check if sessions table has project_id column (in case we're migrating an existing DB)
    cursor.execute("PRAGMA table_info(sessions)")
    columns = {col["name"]: col for col in cursor.fetchall()}
    if "project_id" not in columns:
        cursor.execute("ALTER TABLE sessions ADD COLUMN project_id INTEGER NOT NULL DEFAULT 1")

    # Migration: Remove NOT NULL constraints on start_time and category_id
    needs_recreate = False
    if columns.get("start_time") and columns["start_time"]["notnull"] == 1:
        needs_recreate = True
    if columns.get("category_id") and columns["category_id"]["notnull"] == 1:
        needs_recreate = True

    if needs_recreate:
        cursor.executescript("""
            PRAGMA foreign_keys=OFF;
            CREATE TABLE sessions_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                project_id INTEGER NOT NULL DEFAULT 1,
                category_id INTEGER,
                subcategory_id INTEGER,
                notes TEXT DEFAULT '',
                status TEXT DEFAULT 'active' CHECK(status IN ('active','paused','break','completed')),
                total_active_seconds REAL DEFAULT 0,
                total_break_seconds REAL DEFAULT 0,
                total_pause_seconds REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
                FOREIGN KEY (category_id) REFERENCES categories(id),
                FOREIGN KEY (subcategory_id) REFERENCES subcategories(id)
            );
            INSERT INTO sessions_new (id, date, start_time, end_time, project_id, category_id, subcategory_id, notes, status, total_active_seconds, total_break_seconds, total_pause_seconds, created_at)
            SELECT id, date, start_time, end_time, project_id, category_id, subcategory_id, notes, status, total_active_seconds, total_break_seconds, total_pause_seconds, created_at 
            FROM sessions;
            DROP TABLE sessions;
            ALTER TABLE sessions_new RENAME TO sessions;
            PRAGMA foreign_keys=ON;
        """)

    conn.commit()
    conn.close()
