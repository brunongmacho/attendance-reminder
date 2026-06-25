# Changelog

All notable changes to Attendance Reminder are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [1.0.0] — 2026-06-26

### Added

- System tray icon with green/yellow/red status indicator
- Login reminder — fires 1 hour before shift start
- Critical login reminder — large red window with flashing taskbar 10 min before shift
- Work preparation reminder — 5 min before shift start (only if login acknowledged)
- Logout reminder — fires at shift end
- Critical logout reminder — escalates after 60 min overdue
- Windows lock/unlock detection
- Sleep/wake detection
- Automatic US DST detection with manual override
- Dashboard — shows shift times, reminder times, attendance summary
- Settings window — Schedule and General tabs
- Attendance Recovery modal — checklist with copy/open log
- Single-instance mutex
- Auto-start with Windows (registry)
- Configuration persistence with backup/import/export
- Logging to file

### Fixed

- Work preparation reminder no longer loops indefinitely after acknowledging via Done
- Right-click context menu separator rendering on Windows 11
- Hidden tray window showing in taskbar

[1.0.0]: https://github.com/brunongmacho/attendance-reminder/releases/tag/v1.0.0
