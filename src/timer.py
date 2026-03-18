"""
Timer engine — handles start, pause, resume, break, and stop operations.
Tracks active time, break time, and pause time separately.
Persists all events to the time_events table.
"""

import time
from datetime import datetime
from .database import db_session, get_connection


class TimerEngine:
    """Core timer engine that tracks work sessions with pause/break support."""

    # ... __init__, is_running, elapsed_active, etc ...
    def __init__(self):
        self.session_id = None
        self.status = None  # active, paused, break, completed
        self.project_id = None
        self.category_id = None
        self.subcategory_id = None
        self.notes = ""

        # Timestamps for tracking
        self._segment_start = None  # When current segment started
        self._total_active = 0.0
        self._total_break = 0.0
        self._total_pause = 0.0

    @property
    def is_running(self) -> bool:
        return self.status in ("active", "paused", "break")

    @property
    def elapsed_active(self) -> float:
        """Total active (working) seconds including current segment if active."""
        if self.status == "active" and self._segment_start:
            return self._total_active + (time.time() - self._segment_start)
        return self._total_active

    @property
    def elapsed_break(self) -> float:
        """Total break seconds including current segment if on break."""
        if self.status == "break" and self._segment_start:
            return self._total_break + (time.time() - self._segment_start)
        return self._total_break

    @property
    def elapsed_pause(self) -> float:
        """Total paused seconds including current segment if paused."""
        if self.status == "paused" and self._segment_start:
            return self._total_pause + (time.time() - self._segment_start)
        return self._total_pause

    def start(self, project_id: int, category_id: int = None, subcategory_id: int = None, notes: str = "") -> int:
        """Start a new tracking session. Returns session id."""
        if self.is_running:
            raise RuntimeError("A session is already running. Stop it first.")

        now = datetime.now()
        with db_session() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """INSERT INTO sessions (date, start_time, project_id, category_id, subcategory_id, notes, status)
                   VALUES (?, ?, ?, ?, ?, ?, 'active')""",
                (now.strftime("%Y-%m-%d"), now.isoformat(), project_id, category_id, subcategory_id, notes),
            )
            self.session_id = cursor.lastrowid

            # Record start event
            cursor.execute(
                "INSERT INTO time_events (session_id, event_type, timestamp) VALUES (?, 'start', ?)",
                (self.session_id, now.isoformat()),
            )

        self.project_id = project_id
        self.category_id = category_id
        self.subcategory_id = subcategory_id
        self.notes = notes
        self.status = "active"
        self._segment_start = time.time()
        self._total_active = 0.0
        self._total_break = 0.0
        self._total_pause = 0.0

        return self.session_id

    def pause(self):
        """Pause the current session."""
        if self.status != "active":
            raise RuntimeError("Can only pause an active session.")

        now = datetime.now()
        # Accumulate active time
        self._total_active += time.time() - self._segment_start
        self._segment_start = time.time()
        self.status = "paused"

        self._record_event("pause", now)
        self._update_session_status("paused")

    def resume(self):
        """Resume a paused session."""
        if self.status != "paused":
            raise RuntimeError("Can only resume a paused session.")

        now = datetime.now()
        # Accumulate pause time
        self._total_pause += time.time() - self._segment_start
        self._segment_start = time.time()
        self.status = "active"

        self._record_event("resume", now)
        self._update_session_status("active")

    def start_break(self):
        """Switch to break mode."""
        if self.status not in ("active",):
            raise RuntimeError("Can only take a break from an active session.")

        now = datetime.now()
        # Accumulate active time
        self._total_active += time.time() - self._segment_start
        self._segment_start = time.time()
        self.status = "break"

        self._record_event("break_start", now)
        self._update_session_status("break")

    def end_break(self):
        """End break and resume working."""
        if self.status != "break":
            raise RuntimeError("Not currently on break.")

        now = datetime.now()
        # Accumulate break time
        self._total_break += time.time() - self._segment_start
        self._segment_start = time.time()
        self.status = "active"

        self._record_event("break_end", now)
        self._update_session_status("active")

    def stop(self) -> dict:
        """Stop the current session and return summary."""
        if not self.is_running:
            raise RuntimeError("No active session to stop.")

        now = datetime.now()

        # Accumulate final segment
        if self._segment_start:
            elapsed = time.time() - self._segment_start
            if self.status == "active":
                self._total_active += elapsed
            elif self.status == "paused":
                self._total_pause += elapsed
            elif self.status == "break":
                self._total_break += elapsed

        self.status = "completed"

        # Record stop event
        self._record_event("stop", now)

        # Update session with final data
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE sessions SET
                    end_time = ?,
                    status = 'completed',
                    total_active_seconds = ?,
                    total_break_seconds = ?,
                    total_pause_seconds = ?
                   WHERE id = ?""",
                (
                    now.isoformat(),
                    round(self._total_active, 2),
                    round(self._total_break, 2),
                    round(self._total_pause, 2),
                    self.session_id,
                ),
            )

            # Fetch session details for summary
            cursor.execute(
                """SELECT s.*, p.name as project_name, COALESCE(c.name, 'Uncategorized') as category_name,
                          COALESCE(sc.name, 'N/A') as subcategory_name
                   FROM sessions s
                   JOIN projects p ON s.project_id = p.id
                   LEFT JOIN categories c ON s.category_id = c.id
                   LEFT JOIN subcategories sc ON s.subcategory_id = sc.id
                   WHERE s.id = ?""",
                (self.session_id,),
            )
            session = dict(cursor.fetchone())

        # Reset state
        summary = {
            "session_id": self.session_id,
            "project": session["project_name"],
            "category": session["category_name"],
            "subcategory": session["subcategory_name"],
            "notes": session["notes"],
            "date": session["date"],
            "start_time": session["start_time"],
            "end_time": session["end_time"],
            "active_seconds": self._total_active,
            "break_seconds": self._total_break,
            "pause_seconds": self._total_pause,
            "total_seconds": self._total_active + self._total_break + self._total_pause,
        }

        self.session_id = None
        self._segment_start = None

        return summary

    def update_notes(self, notes: str):
        """Update notes for the current session."""
        if not self.session_id:
            raise RuntimeError("No active session.")
        self.notes = notes
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE sessions SET notes = ? WHERE id = ?", (notes, self.session_id))

    def get_current_info(self) -> dict:
        """Get info about the currently running session."""
        if not self.is_running:
            return None

        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT p.name as project_name, COALESCE(c.name, 'Uncategorized') as category_name,
                          COALESCE(sc.name, 'N/A') as subcategory_name
                   FROM sessions s
                   JOIN projects p ON s.project_id = p.id
                   LEFT JOIN categories c ON s.category_id = c.id
                   LEFT JOIN subcategories sc ON s.subcategory_id = sc.id
                   WHERE s.id = ?""",
                (self.session_id,),
            )
            row = cursor.fetchone()

            return {
                "session_id": self.session_id,
                "status": self.status,
                "project": row["project_name"],
                "category": row["category_name"],
                "subcategory": row["subcategory_name"],
                "notes": self.notes,
                "active_seconds": self.elapsed_active,
                "break_seconds": self.elapsed_break,
                "pause_seconds": self.elapsed_pause,
            }

    def _record_event(self, event_type: str, dt: datetime):
        """Record a time event."""
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO time_events (session_id, event_type, timestamp) VALUES (?, ?, ?)",
                (self.session_id, event_type, dt.isoformat()),
            )

    def _update_session_status(self, status: str):
        """Update the session status in the database."""
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sessions SET status = ? WHERE id = ?", (status, self.session_id)
            )


def format_duration(seconds: float) -> str:
    """Format seconds into HH:MM:SS string."""
    seconds = max(0, int(seconds))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def get_sessions_by_date(date_str: str = None) -> list:
    """Get all completed sessions for a given date (default: today)."""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT s.*, p.name as project_name, COALESCE(c.name, 'Uncategorized') as category_name, c.color as category_color,
                      COALESCE(sc.name, 'N/A') as subcategory_name
               FROM sessions s
               JOIN projects p ON s.project_id = p.id
               LEFT JOIN categories c ON s.category_id = c.id
               LEFT JOIN subcategories sc ON s.subcategory_id = sc.id
               WHERE s.date = ? AND s.status = 'completed'
               ORDER BY s.start_time""",
            (date_str,),
        )
        return [dict(r) for r in cursor.fetchall()]


def get_sessions_in_range(start_date: str, end_date: str) -> list:
    """Get all completed sessions within a date range."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT s.*, p.name as project_name, COALESCE(c.name, 'Uncategorized') as category_name, c.color as category_color,
                      COALESCE(sc.name, 'N/A') as subcategory_name
               FROM sessions s
               JOIN projects p ON s.project_id = p.id
               LEFT JOIN categories c ON s.category_id = c.id
               LEFT JOIN subcategories sc ON s.subcategory_id = sc.id
               WHERE s.date BETWEEN ? AND ? AND s.status = 'completed'
               ORDER BY s.date, s.start_time""",
            (start_date, end_date),
        )
        return [dict(r) for r in cursor.fetchall()]


def get_daily_summary(date_str: str = None) -> dict:
    """Get a summary of time spent by category for a given date."""
    sessions = get_sessions_by_date(date_str)

    summary = {}
    total_active = 0.0
    total_break = 0.0

    for s in sessions:
        cat = s["category_name"]
        if cat not in summary:
            summary[cat] = {
                "active_seconds": 0.0,
                "break_seconds": 0.0,
                "session_count": 0,
                "color": s.get("category_color", "#5B9BD5"),
            }
        summary[cat]["active_seconds"] += s["total_active_seconds"] or 0
        summary[cat]["break_seconds"] += s["total_break_seconds"] or 0
        summary[cat]["session_count"] += 1
        total_active += s["total_active_seconds"] or 0
        total_break += s["total_break_seconds"] or 0

    return {
        "by_category": summary,
        "total_active": total_active,
        "total_break": total_break,
        "total_sessions": len(sessions),
        "date": date_str or datetime.now().strftime("%Y-%m-%d"),
    }
