# Developer Journal

## v1.0.0 — 🚀 First Successful Overnight Shift

### Why this project exists

I work overnight and need to log into my attendance system at 10 PM (DST) / 10:59 PM (Standard) and log out at 7 AM / 8 AM. Missing attendance is not an option. I searched for a simple reminder app but nothing on the market understands shift-based schedules, DST, or the aggressive persistence needed when you're deep in a work flow.

So I built it myself.

### The first real bug

The Work Preparation reminder kept firing every 30 seconds even after clicking Done. The root cause was that "acknowledge" was implemented as a snooze — the Done button cleared the popup reference but left no state flag, so the next timer tick immediately recreated it.

Fix: a proper `work_prep_acknowledged` state flag with JSON persistence, checked before any popup is shown. This also uncovered that the original architecture relied on snooze timers for all acknowledgement logic. Login and logout used the same pattern, just happened to work because their snooze windows were longer.

The lesson: snooze and acknowledge are different concepts. Snooze is temporary. Acknowledge is permanent (until next day). State flags, not timers.

### What I learned about Windows system tray

Windows 11 doesn't reliably fire `NIN_SELECT` for `Shell_NotifyIcon` callbacks. The original `pystray` library couldn't handle this. The fix was a native `win32gui` implementation with a hidden `WS_POPUP` window and a subclassed `WndProc` listening for `WM_CONTEXTMENU` and `WM_LBUTTONUP` directly.

### Architecture decisions that paid off

- Modular `app/` package with separate modules for config, schedule, monitoring, UI, tray, and core
- `ConfigManager` with auto-backup — saved us when experimenting with settings
- Native Win32 API calls instead of wrappers — more control, fewer surprises
- Logging from day one — debugging the work prep bug took minutes because logs were already there

### What's next

- Commander Ralph
- Discord bot integration (personal server)
- Web dashboard
- Android companion app

---

*"Treat this project like it is the foundation of something much larger."*
