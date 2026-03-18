# DevTracker —# Regression Test Log

## Latest Verification Run (2026-03-16)
**Researcher**: Antigravity Assistant

### Fixed Issues
- **Session Update SQL Error**: Resolved `AttributeError` by using correct bracket access for `sqlite3.Row` and handled `None` values robustly.
- **Database Connection Leaks**: Refactored modules to use `db_session` context manager, resolving "database is locked" errors.
- **Missing Dependencies**: Installed `openpyxl`, `reportlab`, and `python-docx` for export functionality.

### Verification Steps
1. **Restart Application**: Ensure server is running with configured environment variables.
2. **Run Tests**: Execute `python regression.py`.
3. **Verify Exports**: Check the `exports/` directory for generated files.

### Manual Verification Results
- **Excel Export**: File generated correctly.
- **PDF Export**: File generated correctly.
- **Word Export**: File generated correctly.
- **Database state**: No locks observed during concurrent testing.

## Overview

This document defines the regression tests for the DevTracker productivity tracker. Run these tests after any code change to verify core functionality.

**URL:** `http://localhost:9876`
**Prerequisites:** `docker-compose build && docker-compose up -d`

---

## Test Cases

### TC-01: Page Load
| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `http://localhost:9876` | Page loads |
| 2 | Check header | Shows "DevTracker v1.0.0" with Categories, Projects, Export buttons and Theme Toggle |
| 3 | Check theme toggle | Clicking toggle switches between Light and Dark modes |
| 4 | Check timer | Shows `00:00` with "READY" status badge |
| 5 | Check sidebar | "Today's Overview" with stats, "Time Breakdown" panel |
| 6 | Check tabs | Today (active), History, Calendar, Totals, Export tabs visible |

### TC-02: Start Timer
| Step | Action | Expected |
|------|--------|----------|
| 1 | Select "Project" from Project dropdown | Selected |
| 2 | Keep "Category" unselected, or select "Coding" | Subcategory dropdown populates (if selected) |
| 3 | Keep "Subcategory" unselected, or select "Feature Development" | Selected |
| 4 | Type notes in Notes field | Text appears |
| 4 | Click "Start Tracking" | Status → "WORKING" (green), timer counts up |
| 5 | Verify controls | Pause, Break, Stop buttons visible |

### TC-03: Pause / Resume
| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "Pause" | Status → "PAUSED" (yellow), Resume button appears |
| 2 | Verify timer | Active time stops counting, Pause time ticks up |
| 3 | Click "Resume" | Status → "WORKING" (green), timer resumes |

### TC-04: Break
| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "Break" | Status → "ON BREAK" (blue), End Break button appears |
| 2 | Verify break time | Break counter ticks up |
| 3 | Click "End Break" | Status → "WORKING" |

### TC-05: Stop Session (Bug Fix Verification)
| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "Stop" | **Custom modal** appears: "Stop Session?" |
| 2 | Click "Cancel" | Modal closes, timer continues |
| 3 | Click "Stop" again | Modal appears again |
| 4 | Click "Stop Session" | Timer resets to 00:00, status → "READY" |
| 5 | Verify toast | "Session complete!" success notification |
| 6 | ⚠️ Previous bug | Browser `confirm()` was instantly dismissed by 1s polling |

### TC-06: Today Tab — Session List
| Step | Action | Expected |
|------|--------|----------|
| 1 | Check today tab | Completed session appears with category, time, notes |
| 2 | Check sidebar stats | Active Time, Sessions count, Top Category updated |
| 3 | Check Time Breakdown | Category bar chart shows time distribution |
| 4 | Verify edit/delete icons | Pencil (✏️) and trash (🗑) icons on each session |

### TC-07: Add Manual Session
| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "+ Add Entry" button | Session modal opens |
| 2 | Set Date to today | Date field populated |
| 3 | Set 'Time Range' or 'Duration' mode | Verify modes switch correctly |
| 4 | If Range: Set 08:00 to 09:30. If Duration: Enter "1.5h". | Value accepted |
| 5 | Select project "Default Project" | Selected |
| 6 | Leave Category blank or select "Debugging" | Optional categories supported |
| 7 | Type notes "Manual entry test" | Notes entered |
| 8 | Click "Save Session" | Modal closes, session appears in Today tab |
| 9 | Verify active time | Should show 01:30:00 |

### TC-08: Edit Session
| Step | Action | Expected |
|------|--------|----------|
| 1 | Click edit icon (✏️) on a session | Edit modal opens |
| 2 | Change category or time | Fields editable |
| 3 | Click "Update Session" | Modal closes, session updated in list |

### TC-09: Delete Session
| Step | Action | Expected |
|------|--------|----------|
| 1 | Click delete icon (🗑) on a session | Confirm modal: "Delete Session?" |
| 2 | Click "Cancel" | Modal closes, session remains |
| 3 | Click delete again, then "Delete" | Session removed from list |
| 4 | Verify stats update | Sidebar stats reflect the deletion |

### TC-10: History Tab
| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "History" tab | Date range fields shown (default: last 7 days) |
| 2 | Click search button | Sessions for the date range appear |
| 3 | Verify summary line | "N sessions · Active: HH:MM · Break: HH:MM" |
| 4 | Verify edit/delete icons | Present on each session |
| 5 | Verify "+ Add" button | Visible in toolbar |
| 6 | Verify "Export" button | Appears after search results load |

### TC-11: Export from History
| Step | Action | Expected |
|------|--------|----------|
| 1 | In History tab, click "Export" button | Switches to Export tab with date range copied |
| 2 | Toast notification | "Date range copied — choose format and export" |

### TC-12: Export Report
| Step | Action | Expected |
|------|--------|----------|
| 1 | In Export tab, select date range | Dates populated |
| 2 | Select "Excel" format | Excel option highlighted |
| 3 | Click "Generate Report" | Success toast, file downloads |
| 4 | Repeat for "PDF" | PDF downloads |
| 5 | Repeat for "Word" | Word doc downloads |
| 6 | Verify files in `./exports/` | Files exist on host machine |

### TC-13: Category Management
| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "Categories" in header | Modal opens with 11 core categories |
| 2 | Verify core categories | Admin, Code Review, Coding, Debugging, DevOps, Documentation, Meetings, Planning, Research, Testing, Troubleshooting |
| 3 | Core categories show "CORE" badge | No delete button on core categories |
| 4 | Click edit (✏️) on Category | Inline edit field shows, can save new name |
| 5 | Click "+ Sub" on a category | Prompt for subcategory name |
| 6 | Click edit (✏️) on Subcategory | Inline edit field shows, can save new name |
| 7 | Enter new name and confirm | Subcategory added |
| 8 | Type new category name, click "+ Add" | Custom category created with "Custom" badge and delete button |
| 9 | Click "Delete" on custom category | Category removed |

### TC-14: Project Management
| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "Projects" in header | Modal opens |
| 2 | Type new project name, click "+ Add" | Custom project created with delete button |
| 3 | Click edit (✏️) on Project | Inline edit field shows, can save new name |
| 4 | Click "Delete" on custom project | Project removed |

### TC-15: Totals Dashboard
| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "Totals" Tab | Totals Dashboard opens |
| 2 | Click "Day", "Week", "Month", "Year" | Fetches and displays stats dynamically without reload |
| 3 | Verify Time Totals | Total Active Time, Break Time, and Sessions update based on history |
| 4 | Verify Category Breakdown | Shows dynamic horizontal bars visualizing time spent |

---

### TC-16: Multi-date Session Entry (Calendar)
| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "+ Add Entry" | Session modal opens with interactive calendar |
| 2 | Click 3 different dates in the calendar | 3 dates are highlighted in blue |
| 3 | Click one of the highlighted dates again | Date deselects (highlight removed) |
| 4 | Click arrows to navigate to next month | Month changes, previous selections preserved |
| 5 | Select project and category | Fields populated |
| 6 | Set Time Range 09:00–10:00 | Values accepted |
| 7 | Click "Save Session" | Toast: "2 session(s) created!" (on current month's selections) |
| 8 | Verify in History tab | Sessions appear on all highlighted dates |

### TC-17: Time Randomizer
| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "+ Add Entry" | Modal opens |
| 2 | Add 2 dates | 2 date chips |
| 3 | Enable "Randomize times within range" | Toggle turns green, randomizer fields appear |
| 4 | Set Earliest Start: 08:00, Latest End: 17:00 | Values accepted |
| 5 | Set Min Duration: 1.0, Max Duration: 2.0 | Values accepted |
| 6 | Click "Save Session" | Toast: "2 session(s) created!" |
| 7 | Verify in History | Sessions have different random start/end times |

### TC-18: Daily Goal Progress Ring
| Step | Action | Expected |
|------|--------|----------|
| 1 | Check sidebar | "Daily Goal" card visible with progress ring |
| 2 | Verify ring shows 0% initially | Ring empty (or reflects today’s data) |
| 3 | Add a session for today | Progress ring updates |
| 4 | Change target from 9 to 4 hours | Toast: "Daily target set to 4h" |
| 5 | Verify ring percentage increases | Percentage recalculated |
| 6 | Refresh page | Target persists at 4 hours |

---

## Last Test Run

| Date | Result | Notes |
|------|--------|-------|
| 2026-03-12 | ✅ All 15 passed | Full browser test with Antigravity browser tool |
| 2026-03-13 | ✅ Pass | TC-16, TC-17, TC-18 passed (Calendar/Goal features) |
| 2026-03-15 | ✅ Pass | TC-19 passed (Time Format Toggle) |
