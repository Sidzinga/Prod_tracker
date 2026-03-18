"""
Project management — CRUD for projects.
"""

from .database import db_session, get_connection

def get_all_projects():
    """Return all projects."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY name")
        return [dict(r) for r in cursor.fetchall()]

def get_project(project_id: int):
    """Return a single project by id."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def add_project(name: str, description: str = "") -> int:
    """Add a new project. Returns the new project id."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO projects (name, description) VALUES (?, ?)",
            (name, description),
        )
        return cursor.lastrowid

def delete_project(project_id: int) -> bool:
    """Delete a project."""
    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            return cursor.rowcount > 0
        except Exception:
            return False

def rename_project(project_id: int, new_name: str) -> bool:
    """Rename a project."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE projects SET name = ? WHERE id = ?", (new_name, project_id)
        )
        return cursor.rowcount > 0
