"""
Category management — seeding defaults and CRUD for custom categories.
"""

from .database import db_session, get_connection
from .config import DEFAULT_CATEGORIES

# ... CATEGORY_COLORS ...
CATEGORY_COLORS = [
    "#4FC3F7",  # Light Blue
    "#FF7043",  # Deep Orange
    "#66BB6A",  # Green
    "#AB47BC",  # Purple
    "#FFA726",  # Orange
    "#26C6DA",  # Cyan
    "#EF5350",  # Red
    "#5C6BC0",  # Indigo
    "#FFCA28",  # Amber
    "#8D6E63",  # Brown
    "#78909C",  # Blue Grey
    "#EC407A",  # Pink
]


def seed_default_categories():
    """Insert default categories and subcategories if they don't exist."""
    with db_session() as conn:
        cursor = conn.cursor()

        for idx, (cat_name, subcats) in enumerate(DEFAULT_CATEGORIES.items()):
            color = CATEGORY_COLORS[idx % len(CATEGORY_COLORS)]
            cursor.execute(
                "INSERT OR IGNORE INTO categories (name, color, is_custom) VALUES (?, ?, 0)",
                (cat_name, color),
            )
            # Get the category id
            cursor.execute("SELECT id FROM categories WHERE name = ?", (cat_name,))
            cat_id = cursor.fetchone()["id"]

            for subcat_name in subcats:
                cursor.execute(
                    "INSERT OR IGNORE INTO subcategories (category_id, name, is_custom) VALUES (?, ?, 0)",
                    (cat_id, subcat_name),
                )


def get_all_categories():
    """Return all categories."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY is_custom, name")
        return [dict(r) for r in cursor.fetchall()]


def get_subcategories(category_id: int):
    """Return all subcategories for a given category."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM subcategories WHERE category_id = ? ORDER BY is_custom, name",
            (category_id,),
        )
        return [dict(r) for r in cursor.fetchall()]


def add_category(name: str, color: str = "#5B9BD5") -> int:
    """Add a custom category. Returns the new category id."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO categories (name, color, is_custom) VALUES (?, ?, 1)",
            (name, color),
        )
        return cursor.lastrowid


def add_subcategory(category_id: int, name: str) -> int:
    """Add a custom subcategory. Returns the new subcategory id."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO subcategories (category_id, name, is_custom) VALUES (?, ?, 1)",
            (category_id, name),
        )
        return cursor.lastrowid


def delete_category(category_id: int) -> bool:
    """Delete a custom category and its subcategories. Returns True if deleted."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT is_custom FROM categories WHERE id = ?", (category_id,)
        )
        row = cursor.fetchone()
        if not row or not row["is_custom"]:
            return False
        cursor.execute("DELETE FROM subcategories WHERE category_id = ?", (category_id,))
        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        return True


def delete_subcategory(subcategory_id: int) -> bool:
    """Delete a custom subcategory. Returns True if deleted."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT is_custom FROM subcategories WHERE id = ?", (subcategory_id,)
        )
        row = cursor.fetchone()
        if not row or not row["is_custom"]:
            return False
        cursor.execute("DELETE FROM subcategories WHERE id = ?", (subcategory_id,))
        return True


def rename_category(category_id: int, new_name: str) -> bool:
    """Rename a category."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE categories SET name = ? WHERE id = ?", (new_name, category_id)
        )
        return cursor.rowcount > 0


def rename_subcategory(subcategory_id: int, new_name: str) -> bool:
    """Rename a subcategory."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE subcategories SET name = ? WHERE id = ?", (new_name, subcategory_id)
        )
        return cursor.rowcount > 0
