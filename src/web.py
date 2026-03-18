"""
DevTracker Web Server — Flask-based API and GUI for the productivity tracker.
Serves the web interface and provides REST API endpoints.
"""

import os
import json
import random
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory, send_file

from .database import initialize_db, db_session, get_connection
from .categories import (
    seed_default_categories, get_all_categories, get_subcategories,
    add_category, add_subcategory, delete_category, delete_subcategory,
    rename_category, rename_subcategory
)
from .projects import get_all_projects, add_project, delete_project, rename_project
from .timer import (
    TimerEngine, format_duration, get_sessions_by_date,
    get_daily_summary, get_sessions_in_range,
)
from .exporter import export_report
from .config import APP_NAME, APP_VERSION, EXPORTS_DIR, DB_PATH

app = Flask(__name__, static_folder="../static", static_url_path="/static")

# Global timer instance (single-user app)
timer = TimerEngine()


# ─────────────────────────── STATIC FILES ───────────────────────────

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# Settings
@app.route("/api/settings", methods=["GET"])
def get_settings():
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        settings = {row["key"]: row["value"] for row in cursor.fetchall()}
        return jsonify(settings)


@app.route("/api/settings", methods=["POST"])
def update_settings():
    data = request.json
    with db_session() as conn:
        cursor = conn.cursor()
        for key, value in data.items():
            cursor.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?",
                (key, value, value),
            )
        return jsonify({"status": "success"})


# ─────────────────────────── API: APP INFO ───────────────────────────

@app.route("/api/info")
def app_info():
    return jsonify({"name": APP_NAME, "version": APP_VERSION})


# ─────────────────────────── API: PROJECTS ───────────────────────────

@app.route("/api/projects")
def list_projects():
    return jsonify(get_all_projects())

@app.route("/api/projects", methods=["POST"])
def create_project():
    data = request.json
    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    try:
        project_id = add_project(name, description)
        return jsonify({"id": project_id, "name": name}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/projects/<int:project_id>", methods=["DELETE"])
def remove_project(project_id):
    if delete_project(project_id):
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Cannot delete project or project not found"}), 400

@app.route("/api/projects/<int:project_id>", methods=["PUT"])
def update_project(project_id):
    data = request.json
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if rename_project(project_id, name):
        return jsonify({"status": "updated"})
    return jsonify({"error": "Project not found or rename failed"}), 400

# ─────────────────────────── API: CATEGORIES ───────────────────────────

@app.route("/api/categories")
def list_categories():
    cats = get_all_categories()
    for cat in cats:
        cat["subcategories"] = get_subcategories(cat["id"])
    return jsonify(cats)


@app.route("/api/categories", methods=["POST"])
def create_category():
    data = request.json
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    try:
        cat_id = add_category(name)
        return jsonify({"id": cat_id, "name": name}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/categories/<int:cat_id>/subcategories", methods=["POST"])
def create_subcategory(cat_id):
    data = request.json
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    try:
        sub_id = add_subcategory(cat_id, name)
        return jsonify({"id": sub_id, "name": name}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/categories/<int:cat_id>", methods=["DELETE"])
def remove_category(cat_id):
    if delete_category(cat_id):
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Cannot delete core categories"}), 400

@app.route("/api/categories/<int:cat_id>", methods=["PUT"])
def update_category(cat_id):
    data = request.json
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if rename_category(cat_id, name):
        return jsonify({"status": "updated"})
    return jsonify({"error": "Category not found or rename failed"}), 400

@app.route("/api/categories/<int:cat_id>/subcategories/<int:sub_id>", methods=["PUT"])
def update_subcategory(cat_id, sub_id):
    data = request.json
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if rename_subcategory(sub_id, name):
        return jsonify({"status": "updated"})
    return jsonify({"error": "Subcategory not found or rename failed"}), 400

@app.route("/api/subcategories/<int:sub_id>", methods=["DELETE"])
def remove_subcategory(sub_id):
    if delete_subcategory(sub_id):
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Cannot delete core subcategories"}), 400


# ─────────────────────────── API: TIMER ───────────────────────────

@app.route("/api/timer/status")
def timer_status():
    if not timer.is_running:
        return jsonify({"running": False})

    info = timer.get_current_info()
    return jsonify({
        "running": True,
        "session_id": info["session_id"],
        "status": info["status"],
        "project": info["project"],
        "category": info["category"],
        "subcategory": info["subcategory"],
        "notes": info["notes"],
        "active_seconds": round(info["active_seconds"], 1),
        "break_seconds": round(info["break_seconds"], 1),
        "pause_seconds": round(info["pause_seconds"], 1),
        "active_formatted": format_duration(info["active_seconds"]),
        "break_formatted": format_duration(info["break_seconds"]),
        "pause_formatted": format_duration(info["pause_seconds"]),
    })


@app.route("/api/timer/start", methods=["POST"])
def timer_start():
    if timer.is_running:
        return jsonify({"error": "A session is already running"}), 400

    data = request.json
    project_id = data.get("project_id")
    cat_id = data.get("category_id")  # Now optional
    sub_id = data.get("subcategory_id")
    notes = data.get("notes", "")

    if not project_id:
        return jsonify({"error": "project_id is required"}), 400

    try:
        session_id = timer.start(int(project_id), int(cat_id) if cat_id else None, int(sub_id) if sub_id else None, notes)
        return jsonify({"session_id": session_id, "status": "active"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/timer/pause", methods=["POST"])
def timer_pause():
    try:
        timer.pause()
        return jsonify({"status": "paused"})
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/timer/resume", methods=["POST"])
def timer_resume():
    try:
        timer.resume()
        return jsonify({"status": "active"})
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/timer/break/start", methods=["POST"])
def timer_break_start():
    try:
        timer.start_break()
        return jsonify({"status": "break"})
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/timer/break/end", methods=["POST"])
def timer_break_end():
    try:
        timer.end_break()
        return jsonify({"status": "active"})
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/timer/stop", methods=["POST"])
def timer_stop():
    try:
        summary = timer.stop()
        return jsonify({
            "status": "completed",
            "summary": {
                "session_id": summary["session_id"],
                "project": summary["project"],
                "category": summary["category"],
                "subcategory": summary["subcategory"],
                "notes": summary["notes"],
                "active": format_duration(summary["active_seconds"]),
                "break": format_duration(summary["break_seconds"]),
                "pause": format_duration(summary["pause_seconds"]),
                "total": format_duration(summary["total_seconds"]),
                "active_seconds": round(summary["active_seconds"], 1),
                "break_seconds": round(summary["break_seconds"], 1),
            },
        })
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/timer/notes", methods=["POST"])
def timer_update_notes():
    data = request.json
    notes = data.get("notes", "")
    try:
        timer.update_notes(notes)
        return jsonify({"status": "updated"})
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400




# ─────────────────────────── API: SESSIONS & SUMMARY ───────────────────────────

@app.route("/api/sessions/today")
def sessions_today():
    today = datetime.now().strftime("%Y-%m-%d")
    sessions = get_sessions_by_date(today)
    summary = get_daily_summary(today)
    return jsonify({
        "date": today,
        "sessions": sessions,
        "summary": {
            "total_active": format_duration(summary["total_active"]),
            "total_active_seconds": round(summary["total_active"], 1),
            "total_break": format_duration(summary["total_break"]),
            "total_break_seconds": round(summary["total_break"], 1),
            "total_sessions": summary["total_sessions"],
            "by_category": summary["by_category"],
        },
    })


@app.route("/api/sessions/history")
def sessions_history():
    start = request.args.get("start", (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
    end = request.args.get("end", datetime.now().strftime("%Y-%m-%d"))
    sessions = get_sessions_in_range(start, end)

    # Build summary
    total_active = sum(s["total_active_seconds"] or 0 for s in sessions)
    total_break = sum(s["total_break_seconds"] or 0 for s in sessions)

    return jsonify({
        "start_date": start,
        "end_date": end,
        "sessions": sessions,
        "total_active": format_duration(total_active),
        "total_active_seconds": round(total_active, 1),
        "total_break": format_duration(total_break),
        "total_break_seconds": round(total_break, 1),
        "total_sessions": len(sessions),
    })

@app.route("/api/stats/totals")
def stats_totals():
    period = request.args.get("period", "day")
    now = datetime.now()
    
    if period == "day":
        start_date = now.strftime("%Y-%m-%d")
        end_date = start_date
    elif period == "week":
        start_date = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        end_date = (now + timedelta(days=6 - now.weekday())).strftime("%Y-%m-%d")
    elif period == "month":
        start_date = now.replace(day=1).strftime("%Y-%m-%d")
        # simple end of month trick
        next_month = now.replace(day=28) + timedelta(days=4)
        end_date = (next_month - timedelta(days=next_month.day)).strftime("%Y-%m-%d")
    elif period == "year":
        start_date = now.replace(month=1, day=1).strftime("%Y-%m-%d")
        end_date = now.replace(month=12, day=31).strftime("%Y-%m-%d")
    else:
        return jsonify({"error": "Invalid period"}), 400

    sessions = get_sessions_in_range(start_date, end_date)
    
    total_active = 0.0
    total_break = 0.0
    by_category = {}

    for s in sessions:
        cat = s["category_name"]
        if cat not in by_category:
            by_category[cat] = {
                "active_seconds": 0.0,
                "break_seconds": 0.0,
                "session_count": 0,
                "color": s.get("category_color", "#5B9BD5"),
            }
        by_category[cat]["active_seconds"] += s["total_active_seconds"] or 0
        by_category[cat]["break_seconds"] += s["total_break_seconds"] or 0
        by_category[cat]["session_count"] += 1
        total_active += s["total_active_seconds"] or 0
        total_break += s["total_break_seconds"] or 0

    return jsonify({
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "total_active_seconds": total_active,
        "total_active_formatted": format_duration(total_active),
        "total_break_seconds": total_break,
        "total_break_formatted": format_duration(total_break),
        "total_sessions": len(sessions),
        "by_category": by_category
    })


# ─────────────────────────── API: SESSION MANAGEMENT ───────────────────────────

def _parse_duration_to_seconds(duration):
    """Parse a duration string/number into total seconds."""
    dur_str = str(duration).strip().lower()
    total_minutes = 0.0
    if ":" in dur_str:
        parts = dur_str.split(":")
        h_val = float(parts[0]) if parts[0] else 0.0
        m_val = float(parts[1]) if len(parts) > 1 and parts[1] else 0.0
        total_minutes = h_val * 60 + m_val
    elif "h" in dur_str or "m" in dur_str:
        parts = dur_str.replace(" ", "").split("h")
        if len(parts) == 2:
            h_val = float(parts[0]) if parts[0] else 0.0
            m_val = float(parts[1].replace("m", "")) if parts[1] and parts[1] != "m" else 0.0
            total_minutes = h_val * 60 + m_val
        elif "m" in parts[0]:
            total_minutes = float(parts[0].replace("m", ""))
        else:
            total_minutes = float(parts[0]) * 60
    else:
        total_minutes = float(dur_str) * 60
    return total_minutes * 60


def _insert_session(cursor, date_str, start_iso, end_iso, project_id, cat_id, sub_id, notes, active_seconds):
    """Insert a single completed session row."""
    cursor.execute(
        """INSERT INTO sessions (date, start_time, end_time, project_id, category_id, subcategory_id, notes, status, total_active_seconds, total_break_seconds, total_pause_seconds)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'completed', ?, 0, 0)""",
        (date_str, start_iso, end_iso, int(project_id), int(cat_id) if cat_id else None, int(sub_id) if sub_id else None, notes, round(active_seconds, 2)),
    )
    return cursor.lastrowid


@app.route("/api/sessions", methods=["POST"])
@app.route("/api/sessions", methods=["POST"])
def add_session():
    """Add manual session(s). Supports single date or multi-date with optional time randomization."""
    data = request.json

    project_id = data.get("project_id")
    cat_id = data.get("category_id")
    sub_id = data.get("subcategory_id")
    notes = data.get("notes", "")

    # Support single date or multiple dates
    dates = data.get("dates")  # list of "YYYY-MM-DD" strings
    single_date = data.get("date")
    if not dates and single_date:
        dates = [single_date]
    if not dates:
        return jsonify({"error": "date or dates[] is required"}), 400
    if not project_id:
        return jsonify({"error": "project_id is required"}), 400

    # Randomization parameters
    randomize = data.get("randomize_time", False)
    time_range_start = data.get("time_range_start", "08:00")  # HH:MM
    time_range_end = data.get("time_range_end", "17:00")      # HH:MM
    min_dur_hours = float(data.get("min_duration_hours", 1.0))
    max_dur_hours = float(data.get("max_duration_hours", 2.0))

    # Non-randomized fields
    start_time = data.get("start_time")  # HH:MM
    end_time = data.get("end_time")      # HH:MM
    duration = data.get("duration")

    try:
        created_ids = []
        with db_session() as conn:
            cursor = conn.cursor()
            for date_str in dates:
                if randomize:
                    # Parse time range boundaries
                    range_start_dt = datetime.strptime(f"{date_str} {time_range_start}", "%Y-%m-%d %H:%M")
                    range_end_dt = datetime.strptime(f"{date_str} {time_range_end}", "%Y-%m-%d %H:%M")
                    range_span = (range_end_dt - range_start_dt).total_seconds()

                    # Random duration between min and max (in seconds)
                    dur_sec = random.uniform(min_dur_hours * 3600, max_dur_hours * 3600)
                    if dur_sec > range_span:
                        dur_sec = range_span  # Clamp to range

                    # Random start within the available window
                    max_start_offset = range_span - dur_sec
                    start_offset = random.uniform(0.0, max(0.0, max_start_offset))
                    start_dt = range_start_dt + timedelta(seconds=start_offset)
                    end_dt = start_dt + timedelta(seconds=dur_sec)

                    sid = _insert_session(cursor, date_str, start_dt.isoformat(), end_dt.isoformat(),
                                          project_id, cat_id, sub_id, notes, dur_sec)
                    created_ids.append(sid)
                elif start_time and end_time:
                    start_dt = datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %H:%M")
                    end_dt = datetime.strptime(f"{date_str} {end_time}", "%Y-%m-%d %H:%M")
                    if end_dt <= start_dt:
                        return jsonify({"error": "End time must be after start time"}), 400
                    active_seconds = (end_dt - start_dt).total_seconds()
                    sid = _insert_session(cursor, date_str, start_dt.isoformat(), end_dt.isoformat(),
                                          project_id, cat_id, sub_id, notes, active_seconds)
                    created_ids.append(sid)
                elif duration:
                    try:
                        active_seconds = _parse_duration_to_seconds(duration)
                    except ValueError:
                        return jsonify({"error": "Invalid duration format. Use '2.5', '2h', or '2h 30m'"}), 400
                    sid = _insert_session(cursor, date_str, None, None,
                                          project_id, cat_id, sub_id, notes, active_seconds)
                    created_ids.append(sid)
                else:
                    return jsonify({"error": "Provide start/end times, duration, or enable randomize_time"}), 400

        if len(created_ids) == 1:
            return jsonify({"session_id": created_ids[0], "status": "created"}), 201
        return jsonify({"session_ids": created_ids, "count": len(created_ids), "status": "created"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/sessions/<int:session_id>", methods=["PUT"])
def edit_session(session_id):
    """Edit an existing session."""
    data = request.json

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        session = cursor.fetchone()
        if not session:
            return jsonify({"error": "Session not found"}), 404

        # Build update
        project_id = data.get("project_id") or session["project_id"] or 1
        cat_id = data.get("category_id")
        if cat_id is None:
            cat_id = session["category_id"]
        
        sub_id = data.get("subcategory_id")
        if sub_id is None:
            sub_id = session["subcategory_id"]
            
        date = data.get("date") or session["date"]
        notes = data.get("notes")
        if notes is None:
            notes = session["notes"]
            
        start_time = data.get("start_time")  # Optional HH:MM
        end_time = data.get("end_time")      # Optional HH:MM
        duration = data.get("duration")

        if start_time and end_time:
            # Time range mode
            start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
            if end_dt <= start_dt:
                return jsonify({"error": "End time must be after start time"}), 400
            active_seconds = (end_dt - start_dt).total_seconds()
            cursor.execute(
                """UPDATE sessions SET date=?, start_time=?, end_time=?, project_id=?, category_id=?, subcategory_id=?, notes=?, total_active_seconds=?
                   WHERE id=?""",
                (date, start_dt.isoformat(), end_dt.isoformat(), int(project_id), int(cat_id) if cat_id else None, int(sub_id) if sub_id else None, notes, round(float(active_seconds), 2), session_id),
            )
        elif duration is not None and str(duration).strip():
            try:
                active_seconds = _parse_duration_to_seconds(duration)
            except ValueError:
                return jsonify({"error": "Invalid duration format."}), 400
            cursor.execute(
                """UPDATE sessions SET date=?, start_time=NULL, end_time=NULL, project_id=?, category_id=?, subcategory_id=?, notes=?, total_active_seconds=?
                   WHERE id=?""",
                (date, int(project_id), int(cat_id) if cat_id else None, int(sub_id) if sub_id else None, notes, round(float(active_seconds), 2), session_id),
            )
        else:
            # Metadata update only
            cursor.execute(
                """UPDATE sessions SET date=?, project_id=?, category_id=?, subcategory_id=?, notes=?
                   WHERE id=?""",
                (date, int(project_id), int(cat_id) if cat_id else None, int(sub_id) if sub_id else None, notes, session_id),
            )

        return jsonify({"status": "updated"})


@app.route("/api/sessions/<int:session_id>", methods=["DELETE"])
def delete_session(session_id):
    """Delete a session."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM time_events WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        deleted = cursor.rowcount > 0
    if deleted:
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Session not found"}), 404


# ─────────────────────────── API: EXPORT ───────────────────────────

@app.route("/api/export", methods=["POST"])
def export():
    data = request.json
    fmt = data.get("format", "excel")
    start = data.get("start_date", (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
    end = data.get("end_date", datetime.now().strftime("%Y-%m-%d"))
    project_id = data.get("project_id", "all")
    decimal_format = data.get("decimal_format", False)
    simple_format = data.get("simple_format", False)
    prepared_for = data.get("prepared_for", "")

    try:
        filepath = export_report(fmt, start, end, project_id, decimal_format, simple_format, prepared_for)
        return jsonify({"file": filepath, "filename": os.path.basename(filepath)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/export/download/<filename>")
def download_export(filename):
    return send_file(
        os.path.join(EXPORTS_DIR, filename),
        as_attachment=True,
        download_name=filename,
    )


# ─────────────────────────── STARTUP ───────────────────────────

def create_app():
    """Initialize database and return the Flask app."""
    initialize_db()
    seed_default_categories()
    return app


if __name__ == "__main__":
    create_app()
    app.run(host="0.0.0.0", port=9876, debug=False)
