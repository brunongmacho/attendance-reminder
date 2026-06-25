# Attendance Reminder

[![Version](https://img.shields.io/badge/version-1.0.0-blue)]()
[![Python](https://img.shields.io/badge/python-3.14+-blue)]()
[![Platform](https://img.shields.io/badge/platform-Windows%2011-lightgrey)]()
[![GitHub](https://img.shields.io/badge/github-brunongmacho/attendance--reminder-181717?logo=github)](https://github.com/brunongmacho/attendance-reminder)

A persistent Windows 11 desktop application that prevents missed attendance logs by aggressively reminding you to log in and log out of your attendance system — built for overnight shift workers.

Runs in the system tray, monitors Windows session lock/unlock and sleep/wake events, and provides escalating popup reminders until you explicitly confirm your attendance.

## Schedule

The app auto-detects US DST. Times align to an 8-hour shift starting at 8am Pacific (PHT = UTC+8).

| Event | DST (PDT) | Standard (PST) |
|-------|-----------|----------------|
| Login reminder | 10:00 PM | 10:59 PM |
| Login critical | 10:50 PM | 11:49 PM |
| Work preparation | 10:55 PM | 11:54 PM |
| **Shift start** | **11:00 PM** | **11:59 PM** |
| Logout reminder | 7:00 AM | 8:00 AM |
| Logout critical | 8:00 AM | 9:00 AM |
| **Shift end** | **7:00 AM** | **8:00 AM** |

Reminders fire Mon–Fri login, Tue–Sat logout. No reminders on Sunday. Work preparation only appears if login is acknowledged first.

> Login reminder fires 1 hour before shift start. Critical fires 10 minutes before shift start. Work preparation (if login confirmed) fires 5 minutes before shift start. Closing (X) snoozes for 60 s; clicking Done acknowledges until next day.

## Quick Start

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

## Features

- **System tray** — green/yellow/red status icon with tooltip (shift start/end + login/logout status). Native win32 implementation.
- **Persistent popups** — must check the box and click Done. Closing = snooze (reappears per snooze setting).
- **Critical mode** — large red window with flashing taskbar. Re-shows every 60 s.
- **Work preparation** — popup at 5 min before shift start (only if login confirmed). Close snoozes 60 s, Done acknowledges until next day.
- **Logout escalation** — louder sound at 15 min, taskbar flash at 30 min, critical at 60 min.
- **Unlock detection** — shows reminder immediately if you unlock within the detection window.
- **Wake detection** — shows pending reminders immediately after sleep.
- **DST auto-detect** — switches between Regular and DST schedules automatically.
- **State persistence** — login, logout, and work preparation acknowledged state survives restarts (no false popups on reboot).
- **Attendance Recovery** — modal checklist with clipboard copy and Open Log.
- **Single instance** — only one copy runs at a time.
- **Auto-start** — registers in HKCU Run key (enabled by default).

## Controls

- **Left-click** tray icon → open Dashboard
- **Right-click** tray icon → context menu (Dashboard, Settings, Test Login, Test Logout, Attendance Recovery, Exit)

## Dashboard

Three sections:
- **Shift Times** — shift start and end
- **Reminder Times** — login, critical, work preparation, logout times (chronological)
- **Today's Attendance Summary** — mode, login status + time, logout status + time, last reminder

Plus action buttons: Test Login, Test Logout, View Logs, Settings, Attendance Recovery.

## Settings

Two tabs:

**Schedule** — All times for both Regular and DST modes (login, logout, critical, unlock windows).

**General** — Snooze duration, enable/disable reminders/sound, auto-start, DST auto-detect and manual override, import/export/backup.

## Configuration

```
%APPDATA%\AttendanceReminder\settings.json
```

Backup: `settings.backup.json`, Logs: `attendance_reminder.log` (same directory).
