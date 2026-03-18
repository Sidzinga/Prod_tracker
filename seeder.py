import sqlite3
import datetime
import os

# Automatically resolve the path to tracker.db
# If running locally, this resolves to ./data/tracker.db
# If running inside Docker, the volume mounts ./data to /app/data
db_path = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tracker.db"))

def get_connection():
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}.")
        print("Please ensure you are running this script from the root of the project or that the tracker has been initialized.")
        exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys just in case
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def get_or_create_category(cursor, category_name, color="#9E9E9E"):
    if not category_name:
        return None
    cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
    row = cursor.fetchone()
    if row:
        return row['id']
    
    # Create as custom category if it doesn't exist
    cursor.execute("INSERT INTO categories (name, color, is_custom) VALUES (?, ?, 1)", (category_name, color))
    return cursor.lastrowid

def get_or_create_subcategory(cursor, category_id, subcategory_name):
    if not subcategory_name or not category_id:
        return None
    cursor.execute("SELECT id FROM subcategories WHERE category_id = ? AND name = ?", (category_id, subcategory_name))
    row = cursor.fetchone()
    if row:
        return row['id']
    
    # Create as custom subcategory if it doesn't exist
    cursor.execute("INSERT INTO subcategories (category_id, name, is_custom) VALUES (?, ?, 1)", (category_id, subcategory_name))
    return cursor.lastrowid

def seed_session(date_str, start_time_str, end_time_str, notes, category_name=None, subcategory_name=None, project_id=1):
    """
    Inserts a completed session into the database.
    
    :param date_str: String format "YYYY-MM-DD" e.g., "2026-03-12"
    :param start_time_str: String format "YYYY-MM-DDTHH:MM:SS" e.g., "2026-03-12T12:00:00"
    :param end_time_str: String format "YYYY-MM-DDTHH:MM:SS" e.g., "2026-03-12T13:00:00"
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cat_id = get_or_create_category(cursor, category_name)
    subcat_id = get_or_create_subcategory(cursor, cat_id, subcategory_name)
    
    start_dt = datetime.datetime.fromisoformat(start_time_str)
    end_dt = datetime.datetime.fromisoformat(end_time_str)
    total_seconds = (end_dt - start_dt).total_seconds()
    
    # Insert session
    cursor.execute('''
        INSERT INTO sessions (
            date, start_time, end_time, project_id, category_id, subcategory_id,
            notes, status, total_active_seconds
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'completed', ?)
    ''', (
        date_str, start_dt.isoformat(), end_dt.isoformat(), project_id, cat_id, subcat_id,
        notes, total_seconds
    ))
    
    session_id = cursor.lastrowid
    
    # Insert time events (required for accurate timeline rendering if needed)
    cursor.execute("INSERT INTO time_events (session_id, event_type, timestamp) VALUES (?, 'start', ?)",
                   (session_id, start_dt.isoformat()))
    cursor.execute("INSERT INTO time_events (session_id, event_type, timestamp) VALUES (?, 'stop', ?)",
                   (session_id, end_dt.isoformat()))
    
    conn.commit()
    conn.close()
    print(f"Successfully seeded session: '{notes}' on {date_str} from {start_dt.strftime('%H:%M')} to {end_dt.strftime('%H:%M')}")

if __name__ == "__main__":
    print("-------- DevTracker Generic Seeder --------")
    
    # =========================================================================
    # EDIT THE COMMANDS BELOW TO ADD YOUR REPETITIVE EVENTS (LUNCH, TESTING...)
    # =========================================================================
    
    # Example 1: Add a Lunch break
    # seed_session(
    #     date_str="2026-03-12",
    #     start_time_str="2026-03-12T12:00:00",
    #     end_time_str="2026-03-12T13:00:00",
    #     notes="Lunch break",
    #     category_name="Admin",
    #     subcategory_name="Break"
    # )
    
    # Example 2: Add a Testing session
    # seed_session(
    #     date_str="2026-03-12",
    #     start_time_str="2026-03-12T14:00:00",
    #     end_time_str="2026-03-12T15:30:00",
    #     notes="Manual QA & Testing",
    #     category_name="Testing",
    #     subcategory_name="Manual QA"
    # )
    
    # Add your own events here...
    
    
    
    print("\nDone. If no events were added, remember to uncomment or add seed_session(...) commands in this file.")
