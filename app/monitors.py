"""
System monitors for Attendance Reminder.

Tracks Windows workstation lock/unlock state (background thread) and detects
sleep/wake transitions via time-gap polling.
"""

import time
import logging
import threading
from datetime import datetime

from .utils import is_workstation_locked, UNLOCK_POLL_INTERVAL


class SessionMonitor:
    """
    Monitors workstation lock/unlock in a daemon background thread.

    Calls the provided callback when a transition from locked to unlocked
    is detected.
    """

    def __init__(self, on_unlock_callback):
        self.on_unlock = on_unlock_callback
        self._running = False
        self._thread = None
        self._prev_locked = is_workstation_locked()

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _run(self):
        while self._running:
            try:
                locked = is_workstation_locked()
                if self._prev_locked and not locked:
                    if self.on_unlock:
                        self.on_unlock()
                self._prev_locked = locked
                time.sleep(UNLOCK_POLL_INTERVAL)
            except Exception as e:
                logging.error("Session monitor error: %s", e)
                time.sleep(5)


class PowerMonitor:
    """
    Detects sleep/wake by checking elapsed time between polls.

    If more than *threshold_seconds* have passed since the last check,
    a wake event is assumed and the callback is invoked.
    """

    def __init__(self, on_wake_callback, threshold_seconds=120):
        self.on_wake = on_wake_callback
        self.threshold = threshold_seconds
        self._last_check = datetime.now()

    def check(self):
        """Call periodically from the main loop. Returns True if wake detected."""
        now = datetime.now()
        elapsed = (now - self._last_check).total_seconds()
        self._last_check = now
        if elapsed > self.threshold:
            if self.on_wake:
                self.on_wake()
            return True
        return False


class DailySummary:
    """
    Tracks daily attendance events (login/logout shown time, confirmed time,
    and attendance verification checkpoints). Generates a formatted summary
    string for logging at day rollover.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.today = datetime.now().date()
        self.login_reminder_shown = None
        self.login_confirmed = None
        self.logout_reminder_shown = None
        self.logout_confirmed = None


    def is_new_day(self):
        return datetime.now().date() != self.today

    def log_login_reminder(self):
        self.login_reminder_shown = datetime.now()

    def log_login_confirmed(self):
        self.login_confirmed = datetime.now()

    def log_logout_reminder(self):
        self.logout_reminder_shown = datetime.now()

    def log_logout_confirmed(self):
        self.logout_confirmed = datetime.now()

    @property
    def last_reminder_shown(self):
        candidates = []
        if self.login_reminder_shown:
            candidates.append(self.login_reminder_shown)
        if self.logout_reminder_shown:
            candidates.append(self.logout_reminder_shown)
        return max(candidates) if candidates else None

    def generate_summary(self):
        """Produce a formatted daily summary string for the log."""
        from .utils import DATETIME_FORMAT
        fmt = DATETIME_FORMAT
        lr = self.login_reminder_shown.strftime(fmt) if self.login_reminder_shown else "N/A"
        lc = self.login_confirmed.strftime(fmt) if self.login_confirmed else "N/A"
        or_ = self.logout_reminder_shown.strftime(fmt) if self.logout_reminder_shown else "N/A"
        oc = self.logout_confirmed.strftime(fmt) if self.logout_confirmed else "N/A"
        sep = "=" * 45
        return (
            f"\n{sep}\n"
            f"  Daily Summary - {self.today}\n"
            f"{sep}\n"
            f"  Login Reminder Shown:   {lr}\n"
            f"  Login Confirmed:        {lc}\n"
            f"  Logout Reminder Shown:  {or_}\n"
            f"  Logout Confirmed:       {oc}\n"
            f"{sep}"
        )
