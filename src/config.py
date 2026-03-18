import os

DEFAULT_CATEGORIES = {
    "Coding": [
        "Feature Development",
        "Refactoring",
        "Prototyping",
        "Code Cleanup",
        "Bug Fixes",
        "API Development",
    ],
    "Debugging": [
        "Bug Investigation",
        "Log Analysis",
        "Breakpoint Debugging",
        "Performance Profiling",
        "Memory Leak Analysis",
    ],
    "Troubleshooting": [
        "Environment Issues",
        "Dependency Conflicts",
        "Build Failures",
        "Integration Issues",
        "Network / Connectivity",
        "Configuration Errors",
    ],
    "Code Review": [
        "PR Review",
        "Architecture Review",
        "Pair Programming",
        "Code Walkthrough",
    ],
    "Testing": [
        "Unit Testing",
        "Integration Testing",
        "Manual QA",
        "Test Writing",
        "E2E Testing",
        "Test Maintenance",
    ],
    "Documentation": [
        "Technical Docs",
        "API Documentation",
        "README Updates",
        "Architecture Diagrams",
        "Inline Comments",
    ],
    "DevOps": [
        "CI/CD Pipeline",
        "Deployment",
        "Infrastructure",
        "Monitoring & Alerts",
        "Docker / Containers",
    ],
    "Meetings": [
        "Standup",
        "Sprint Planning",
        "Retrospective",
        "1-on-1",
        "Client Call",
        "Team Sync",
    ],
    "Planning": [
        "Ticket Grooming",
        "Estimation",
        "Architecture Design",
        "Roadmap Planning",
        "Sprint Review",
    ],
    "Research": [
        "Technology Evaluation",
        "Spike / PoC",
        "Learning",
        "Reading Documentation",
        "Online Courses",
    ],
    "Admin": [
        "Email",
        "Slack / Chat",
        "Jira / Board Management",
        "Time Reporting",
        "Onboarding",
    ],
}

# Break reminder interval in minutes
DEFAULT_BREAK_REMINDER_MINUTES = 45

# Default export format
DEFAULT_EXPORT_FORMAT = "excel"

# App metadata
APP_NAME = "DevTracker"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Productivity Time Tracker for Software Developers"

# Database path
DB_PATH = os.getenv("DB_PATH", "/app/data/tracker.db")
EXPORTS_DIR = os.getenv("EXPORTS_DIR", "/app/exports")
