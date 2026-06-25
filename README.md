# Attendance Reminder

[![Version](https://img.shields.io/badge/version-1.0.0-blue)]()
[![Python](https://img.shields.io/badge/python-3.14+-blue)]()
[![Platform](https://img.shields.io/badge/platform-Windows%2011-lightgrey)]()
[![GitHub](https://img.shields.io/badge/github-brunongmacho/attendance--reminder-181717?logo=github)](https://github.com/brunongmacho/attendance-reminder)

A Windows desktop application that reminds you to log in and out of your attendance system.

It runs in the system tray, monitors workstation lock and sleep events, and keeps reminding you until you confirm.

---

## Why I Built This

I work overnight shifts. My attendance system requires a login at the start of my shift and a logout at the end. Missing either one creates HR issues.

I tried phone alarms. I tried calendar reminders. I tried sticky notes. None of them understood that my schedule shifts by an hour when daylight saving changes, or that I need different reminders on different days of the week. None of them kept reminding me when I was in the middle of something and snoozed the alert.

So I built the tool I needed.

I am a Mechanical Design Engineer by trade. I learned Python the same way I learned Autodesk Inventor — because I had a real problem to solve and I refused to accept that no tool existed for it. I don't build projects to learn. I learn because I need to build something.

This project exists because engineering a solution was faster than waiting for someone else to build one.

---

## Project Philosophy

- Every feature must solve a real problem.
- Reliability matters more than aesthetics.
- The application should work without me thinking about it.
- Future expansion must never sacrifice current stability.

---

## Features

### Production (v1.0.0)

- System tray icon with green/yellow/red status indicator
- Login reminder — fires one hour before shift start
- Critical login — red window with flashing taskbar ten minutes before shift
- Work preparation — fires five minutes before shift start if login is confirmed
- Logout reminder — fires at shift end
- Critical logout — escalates after one hour overdue (louder, flashing, critical)
- Windows lock/unlock detection
- Sleep/wake detection
- Automatic US DST detection with manual override
- Dashboard showing shift times, reminder timeline, and attendance summary
- Settings window (Schedule and General tabs)
- Attendance Recovery checklist with copy and open log
- Configuration persistence with automatic backup
- Single-instance mutex
- Optional auto-start with Windows

### Planned

- Multi-shift support
- Notification sounds selection
- Weekly summary reports
- Dashboard attendance history
- Calendar integration
- Discord bot companion
- Web dashboard

---

## Screenshots

*(To be added)*

---

## Installation

### Run from source

```cmd
git clone https://github.com/brunongmacho/attendance-reminder.git
cd attendance-reminder
pip install -r requirements.txt
python main.py
```

### Build standalone EXE

```cmd
build.bat
```

The executable will be at `dist\AttendanceReminder.exe`.

Only one instance of the application can run at a time. Closing the window minimizes to the system tray. Right-click the tray icon to exit.

---

## Usage

A normal overnight shift works like this:

1. The application starts automatically with Windows.
2. At 10:00 PM (or 10:59 PM depending on DST), a login reminder appears.
3. You check the box and click Done.
4. At 10:55 PM (or 11:54 PM), a work preparation popup appears. The same rules apply — check and confirm.
5. At 7:00 AM (or 8:00 AM), a logout reminder appears.
6. If you miss any reminder, the application escalates — louder sounds, taskbar flashing, eventually a critical red window that re-appears every sixty seconds.

Snoozing (closing the window) gives you five minutes. Confirming (checking the box and clicking Done) acknowledges the reminder until the next shift.

The tray icon tells you the current status at a glance:

- Green — no reminders pending
- Yellow — a reminder is due
- Red — a reminder is critically overdue

---

## Roadmap

```
v1.0.0 ─── Attendance Reminder
                │
                ▼
v2.0+   ─── Multi-shift, notifications, companion apps
                │
                ▼
v?.?    ─── Commander Ralph
```

Attendance Reminder is the first component of a larger project called **Commander Ralph** — a personal desktop operating system that manages work, reminders, calendar, productivity, automation, and eventually AI assistance.

Every feature added to this project is designed to eventually integrate into that system.

---

## Architecture

The application follows a modular structure:

```
main.py              Entry point, single-instance check
app/
├── config.py        JSON configuration with auto-backup
├── schedule.py      Shift schedule and DST logic
├── monitors.py      Session and power event detection
├── core.py          Application logic and timer loop
├── ui.py            Popup, dashboard, settings windows
├── tray.py          Native Windows system tray
├── utils.py         Constants, helpers, Windows API
└── services/        Future expansion
```

Each module has a single responsibility. The core loop runs every thirty seconds and checks whether any reminder needs to fire. Configuration is persisted to `%APPDATA%\AttendanceReminder\settings.json`.

Windows is the target platform because that is where the attendance system runs and where the application is needed.

---

## Development Philosophy

- `main` is always stable. Never commit directly to it.
- All development happens on `develop` or `feature` branches.
- Before every feature, ask: *"Would Future Ralph actually thank Present Ralph for building this?"*
- If the answer is no, don't build it.
- If the answer is yes, build it properly the first time.

See [CONTRIBUTING.md](CONTRIBUTING.md) if you intend to contribute.

---

## DEVLOG

This repository contains two documents:

- **CHANGELOG.md** — tracks what changed in each version. Useful for anyone using or maintaining the software.
- **DEVLOG.md** — tracks why things were built, what was learned, and where the project is going. This is the developer journal.

The DEVLOG is not a technical document. It is a record of the journey. If you are curious about the story behind a feature, read the DEVLOG.

---

## Future Vision

Commander Ralph will be a personal desktop operating system that grows one useful feature at a time.

It will eventually manage:

- Work reminders and attendance
- Calendar and scheduling
- Daily planning and task management
- Health and break reminders
- Automation of repetitive tasks
- Local AI assistant with voice interaction
- Context-aware workflow suggestions

But none of that matters if the foundation is not stable. That is why Attendance Reminder exists as Version 1 — a single, focused, reliable tool that does one thing well. Everything else will be built on top of that same discipline.

---

## Personal Note

I have spent nine years designing machines that help factories produce food, medicine, and equipment. I learned every CAD skill I have by watching YouTube tutorials and making mistakes until things worked.

I am doing the same thing with Python.

Attendance Reminder is not a portfolio piece. It is not a learning exercise. It is a tool I use every single night to make sure I never miss an attendance log. If it saves me from one HR conversation, it has already paid for itself.

This repository is the beginning of something larger, but it is also a complete and working tool right now.

That is the only way I know how to build anything.
