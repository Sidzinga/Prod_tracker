# Productivity Tracker

A Docker-based **web GUI** productivity tracker that helps software developers track time across categorized activities, with full pause/resume/break support and multi-format report exports.

## Features

- ⏱ **Live Timer** — Start, pause, resume, or enter manual durations for past work sessions
- ☕ **Break Management** — Track breaks separately from active work
- 🗂 **Projects** — Group your tracking sessions by Project top-level entity, and easily rename them
- 📁 **11 Core Categories** — Coding, Debugging, Troubleshooting, Testing, Code Review, Documentation, DevOps, Meetings, Planning, Research, Admin (Categories are optional)
- 🏷 **Subcategories** — Drill down into specific activities (e.g., Debugging → Bug Investigation)
- ✏️ **Custom Categories** — Add, rename, and manage your own categories and subcategories
- 📅 **Multi-date Entry** — Select multiple dates at once and add the same session to all of them
- 🎲 **Time Randomizer** — Randomize start times and durations within configurable ranges
- 🎯 **Daily Goal Progress** — Visual progress ring showing time spent vs. a configurable daily target (default 9 hours)
- 📤 **Export Reports** — Generate detailed Excel (.xlsx), PDF, or Word (.docx) reports including time spent by project and category
- 📈 **Totals Dashboard** — View aggregated time and category breakdown across Day, Week, Month, and Year periods
- 📅 **Session History** — Browse past sessions with date filters
- 💾 **Persistent Storage** — SQLite database stored on your machine via Docker volume
- 🎨 **Light / Dark UI** — Beautiful web interface with a persistent theme toggle

## Quick Start

### Prerequisites
- Docker and Docker Compose installed

### Run

```bash
docker-compose build
docker-compose up -d
```

Then open your browser to **http://localhost:9876**

### Stop

```bash
docker-compose down
```

### Data Persistence

- **Database**: `./data/tracker.db` — your session data persists across container restarts
- **Exports**: `./exports/` — generated reports are saved here, accessible from your host machine

## Usage

### Timer Controls

1. **Select a category** (optional) and a subcategory from the dropdowns
2. **Click "Start Tracking"** to begin your session
3. Use the **Pause**, **Break**, and **Resume** buttons as needed
4. **Click "Stop"** when done — your session is saved automatically

Alternatively, click **Add Entry** to manually submit a past session by entering "Time Spent" duration or a strict Start/End Time block.

### Time Format Toggle
1. Locate the format toggle button in the top toolbar (it displays "12:30" for Normal or "12.5h" for Decimal).
2. Click the button to switch the display format for all time values across the application (Timer, Today's Overview, History, and Totals).
3. Your preference is automatically saved and will persist across sessions.

### Multi-date Entry & Randomizer

1. Click **+ Add Entry** — the modal features an interactive multi-select calendar
2. Click dates in the calendar to highlight them (click again to deselect)
3. Navigate months using the < and > arrows
4. Optionally enable **Randomize times within range** to generate realistic varied entries
5. Click **Save Session** — sessions are created for all highlighted dates

### Daily Goal Progress Ring

- The sidebar shows a **progress ring** visualizing time worked vs. your daily target
- Default target is **9 hours**, editable via the "Target" input
- Colors change based on progress (orange → yellow → green)

### Exporting Reports

1. Click the **Export** tab at the bottom
2. Select a **date range**
3. Choose **Excel**, **PDF**, or **Word** format
4. Click **Generate Report** — the file downloads automatically

### Managing Projects

1. Click the **Projects** button in the header
2. Add custom projects
3. Rename projects by clicking the edit icon in the list
4. Delete projects (default project is protected)

### Managing Categories

1. Click the **Categories** button in the header
2. Add custom categories and subcategories
3. Rename categories and subcategories by clicking their respective edit icons
4. Delete custom categories (core categories are protected)

## Categories

| Category | Example Subcategories |
|----------|----------------------|
| Coding | Feature Dev, Refactoring, Prototyping, Bug Fixes |
| Debugging | Bug Investigation, Log Analysis, Performance Profiling |
| Troubleshooting | Environment Issues, Build Failures, Dependency Conflicts |
| Code Review | PR Review, Pair Programming, Architecture Review |
| Testing | Unit Testing, Integration Testing, Manual QA |
| Documentation | Technical Docs, API Docs, README Updates |
| DevOps | CI/CD, Deployment, Docker / Containers |
| Meetings | Standup, Sprint Planning, Retro, 1-on-1 |
| Planning | Estimation, Architecture Design, Ticket Grooming |
| Research | Spike / PoC, Learning, Technology Evaluation |
| Admin | Email, Slack, Jira / Board Management |

## Project Structure

```
Prod tracker/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── src/
│   ├── main.py          # Entry point (launches web server)
│   ├── web.py           # Flask API server
│   ├── timer.py         # Timer engine
│   ├── projects.py      # Project CRUD
│   ├── categories.py    # Category CRUD
│   ├── database.py      # SQLite setup
│   ├── exporter.py      # Excel/PDF/Word export
│   └── config.py        # Defaults and constants
├── static/
│   └── index.html       # Web GUI (single-page app)
├── data/                # SQLite DB (Docker volume)
└── exports/             # Generated reports (Docker volume)
```

## Tech Stack

- **Backend**: Python 3.12, Flask, SQLite
- **Frontend**: Vanilla HTML/CSS/JS with Material Icons
- **Exports**: openpyxl (Excel), ReportLab (PDF), python-docx (Word)
- **Infra**: Docker + Docker Compose (port 9876)
