import sqlite3
conn=sqlite3.connect('data/tracker.db')
conn.row_factory = sqlite3.Row
cursor=conn.cursor()

cursor.execute("PRAGMA table_info(sessions)")
columns_info = {col["name"]: col for col in cursor.fetchall()}

needs_migration = False
if columns_info.get("start_time") and columns_info["start_time"]["notnull"] == 1:
    needs_migration = True
if columns_info.get("category_id") and columns_info["category_id"]["notnull"] == 1:
    needs_migration = True

print("Needs migration?", needs_migration)

if needs_migration:
    print("Running migration...")
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
    print("Migration complete!")
else:
    print("No migration needed.")

cursor.execute("SELECT sql FROM sqlite_master WHERE name='sessions'")
print("New schema:", cursor.fetchone()[0])
