#!/usr/bin/env python3
"""
Attendance Reminder - Entry Point.

Checks for an existing instance (single-instance enforcement via named
mutex), then launches the Tkinter main loop.
"""

import sys
import tkinter as tk

from app.utils import APP_NAME, get_app_data_dir, is_already_running
from app.core import AttendanceReminderApp


def main():
    """Application entry point."""
    if is_already_running():
        print(f"{APP_NAME} is already running.", file=sys.stderr)
        sys.exit(0)

    app_dir = get_app_data_dir()

    try:
        root = tk.Tk()
        root.withdraw()
        app = AttendanceReminderApp(root, app_dir)
        root.mainloop()
    except Exception as e:
        import logging
        logging.exception("Fatal application error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
