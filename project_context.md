# DevTracker — Project Context

## Purpose

DevTracker is a **personal productivity time tracker** built for software developers. It runs as a Docker container serving a web GUI on **port 9876** and persists data via SQLite.

## Problem Solved

Developers need to track how they spend their work hours across different activities (coding, debugging, meetings, etc.) for time reporting, self-improvement, and project billing. DevTracker provides a simple, always-available tracker that doesn't require any cloud service or account.

---

## Tech Stack

| Layer | Technology | File(s) |
|-------|-----------|---------|
| **Backend** | Python 3.12, Flask | `src/web.py`, `src/timer.py` |
| **Frontend** | Vanilla HTML/CSS/JS, Material Icons, Google Fonts (Inter) | `static/index.html` |
| **Database** | SQLite (WAL mode) | `src/database.py`, `./data/tracker.db` |
| **Exports** | openpyxl, ReportLab, python-docx | `src/exporter.py` |
| **Infra** | Docker, Docker Compose | `Dockerfile`, `docker-compose.yml` |

---

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   Browser (SPA)     │────▶│   Flask API (:9876)  │
│   static/index.html │◀────│   src/web.py         │
└─────────────────────┘     └─────────┬───────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                  ▼
            ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
            │ TimerEngine │  │ Projects/Cat │  │ Exporter     │
            │ timer.py    │  │ proj/cat.py  │  │ exporter.py  │
            └──────┬──────┘  └──────┬───────┘  └──────┬───────┘
                   │                │                  │
                   └────────────────┼──────────────────┘
                                    ▼
                            ┌──────────────┐
                            │   SQLite DB  │
                            │   database.py│
                            └──────────────┘
```

---

## Key Features

1. **Live Timer** — Start/pause/resume/break/stop with real-time UI updates (1s polling)
2. **Projects** — Group your tracking sessions by Project top-level entity
3. **11 Core Categories** — Coding, Debugging, Troubleshooting, Testing, Code Review, Documentation, DevOps, Meetings, Planning, Research, Admin
4. **Subcategories** — Each core category has 4-6 pre-defined subcategories
4. **Custom Categories** — Users can add their own categories and subcategories
5. **Manual Entry** — Add sessions with custom dates and times for past work
6. **Multi-date Entry** — Interactive calendar view allows highlighting multiple dates for bulk session creation
7. **Time Randomizer** — Randomize start/end times and durations within user-defined ranges
8. **Daily Goal Progress** — Conic gradient ring showing % of daily target completed (default 9h, configurable)
9. **Session Editing** — Edit category, time, and notes on existing sessions
10. **Session Deletion** — Delete sessions with confirmation modal
11. **Export Reports** — Detailed or Simple Excel (.xlsx), PDF, Word (.docx) with date range selection. Simple format includes week-by-week grouping (e.g., "Week 1 of Jan") and minimal columns.
12. **Today Dashboard** — Live session list, time breakdown chart, stats summary
13. **History View** — Browse sessions by date range with edit, delete, and export

---

## Project Structure

```
Prod tracker/
├── Dockerfile                      # Python 3.12 slim container
├── docker-compose.yml              # Port 9876, volume mounts
├── requirements.txt                # Python dependencies
├── README.md                       # User-facing documentation
├── regression_test.md              # 13-case test plan
├── db_schema_and_relationships.md  # Database documentation
├── project_context.md              # This file
├── src/
│   ├── __init__.py
│   ├── main.py          # Entry point → launches Flask
│   ├── web.py           # Flask API (all REST endpoints)
│   ├── timer.py         # Timer state machine
│   ├── projects.py      # Project CRUD operations
│   ├── categories.py    # Category CRUD operations
│   ├── database.py      # SQLite schema + connection
│   ├── exporter.py      # Export to Excel/PDF/Word
│   └── config.py        # Constants, defaults, category definitions
├── static/
│   └── index.html       # Single-page web app (dark theme)
├── data/                # SQLite DB (Docker volume)
│   └── tracker.db
└── exports/             # Generated reports (Docker volume)
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serve the web app |
| GET | `/api/info` | App name + version |
| GET | `/api/projects` | List all projects |
| POST | `/api/projects` | Create custom project |
| DELETE | `/api/projects/:id` | Delete custom project |
| GET | `/api/categories` | List all categories with subcategories |
| POST | `/api/categories` | Create custom category |
| DELETE | `/api/categories/:id` | Delete custom category |
| POST | `/api/categories/:id/subcategories` | Add subcategory |
| GET | `/api/timer/status` | Current timer state |
| POST | `/api/timer/start` | Start a session |
| POST | `/api/timer/pause` | Pause session |
| POST | `/api/timer/resume` | Resume session |
| POST | `/api/timer/break/start` | Start break |
| POST | `/api/timer/break/end` | End break |
| POST | `/api/timer/stop` | Stop and save session |
| POST | `/api/timer/notes` | Update session notes |
| GET | `/api/sessions/today` | Today's sessions + summary |
| GET | `/api/sessions/history?start=&end=` | Sessions in date range |
| POST | `/api/sessions` | Add manual session(s) — supports multi-date and randomized times |
| PUT | `/api/sessions/:id` | Edit existing session |
| DELETE | `/api/sessions/:id` | Delete session |
| GET | `/api/settings` | Get user settings (daily target, etc.) |
| POST | `/api/settings` | Update user settings |
| POST | `/api/export` | Generate report (Excel/PDF/Word) |
| GET | `/api/export/download/:filename` | Download generated report |

---

## Configuration

| Setting | Value | Location |
|---------|-------|----------|
| Port | 9876 | `docker-compose.yml`, `src/web.py` |
| DB Path | `/app/data/tracker.db` | `src/config.py` |
| Exports Dir | `/app/exports` | `src/config.py` |
| Host Volumes | `./data`, `./exports` | `docker-compose.yml` |

---

## Known Design Decisions

- **Single-user**: One global `TimerEngine` instance — designed for personal use
- **Port 9876**: Chosen to avoid conflicts with common dev ports (3000, 5000, 8080)
- **No auth**: Local-only tool, no login required
- **SQLite**: Lightweight, no server needed, persisted via Docker volume
- **Polling**: Frontend polls `/api/timer/status` every 1s for live updates
- **Stop modal**: Custom in-page modal instead of `confirm()` — browser confirm was being dismissed by polling

---

## Recent Changes

* **Calendar Live Update (March 2026)**: Saving a new entry or editing an existing one will now automatically refresh the Calendar view without requiring a page reload if the calendar tab is currently active.
* **Database Schema Update (March 2026)**: Added a database migration within `initialize_db` to strip `NOT NULL` constraints from `start_time` and `category_id` in the `sessions` table. This allows users to accurately track time using the "Duration" mode and safely submit uncategorized work without triggering a database integrity error.
* **Calendar Add Entry Fix (March 2026)**: Fixed a bug where clicking a date on the calendar to add an entry would default the dialog's date to "today" instead of the clicked date. The `openSessionModal()` signature was updated to accept a `defaultDateStr`, which is now passed correctly from the calendar grid `onclick` handler to initialize the "multi-date" chips and default date value.
* **Database Robustness and Connection Safety (March 2026)**: Refactored the entire backend connectivity layer to resolve "database is locked" errors common in Windows and Docker environments. This included implementing a `db_session` context manager for atomic transactions, increasing the connection timeout to 20 seconds, and ensuring consistent `sqlite3.Row` access across all API endpoints (fixing the SQL update `AttributeError`).
