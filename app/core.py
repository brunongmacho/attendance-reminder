"""
Core application logic for Attendance Reminder.

AttendanceReminderApp ties together all components: configuration, scheduling,
session/power monitoring, tray icon, and UI windows. It runs a periodic timer
that checks whether reminders need to fire and manages snooze/acknowledgement
state.
"""

import os
import logging
from datetime import datetime, timedelta

import tkinter as tk

from .utils import (
    APP_NAME, APP_DIR_NAME, CHECK_INTERVAL_MS, SNOOZE_DEFAULT_MIN,
    CRITICAL_RESHOW_SEC, ICON_GREEN, ICON_YELLOW, ICON_RED, LOG_FILE,
    play_notification_sound, set_auto_start, setup_logging,
)
from .config import ConfigManager
from .schedule import ScheduleManager
from .monitors import SessionMonitor, PowerMonitor, DailySummary
from .tray import TrayManager
from .ui import PopupWindow, CriticalWindow, DashboardWindow, SettingsWindow


class AttendanceReminderApp:
    """Main application class coordinating all sub-systems."""

    def __init__(self, root, app_dir):
        self.root = root
        self.app_dir = app_dir
        self.log_path = app_dir / LOG_FILE

        setup_logging(self.log_path)

        logging.info("%s", "=" * 50)
        logging.info("  %s Starting", APP_NAME)
        logging.info("%s", "=" * 50)
        logging.info("App directory: %s", app_dir)

        self.config = ConfigManager(app_dir)
        self.schedule_manager = ScheduleManager(self.config)
        self.daily_summary = DailySummary()
        self.session_monitor = SessionMonitor(self._on_unlock)
        self.power_monitor = PowerMonitor(self._on_wake)
        self.tray = TrayManager(self)

        self.settings_window = None
        self.dashboard_window = None

        self._login_popup = None
        self._logout_popup = None
        self._critical_login_popup = None
        self._critical_logout_popup = None

        self.state = {
            "login_acknowledged": False,
            "logout_acknowledged": False,
            "work_prep_acknowledged": False,
            "login_reminder_first_shown": None,
            "logout_reminder_first_shown": None,
        }
        self._login_snooze_until = None
        self._logout_snooze_until = None
        self._work_prep_popup = None
        self._work_prep_snooze_until = None

        self._running = True

        self.root.protocol("WM_DELETE_WINDOW", self._on_root_close)

        # Start subsystems
        self.tray.start()
        self.session_monitor.start()

        dst = self.config.is_dst_active()
        mode = "US DST" if dst else "Regular"
        logging.info("Schedule mode: %s (DST auto: %s)",
                      mode, self.config.get("dst_auto_detect"))
        set_auto_start(self.config.get("auto_start", False))
        self.root.after(2000, self._timer_tick)

        if not self.config.get("reminders_enabled", True):
            logging.info("Reminders are disabled in settings")

        self._restore_daily_state()
        self._log_initial_state()

    # ------------------------------------------------------------------
    # Sound helper (used as self.sound_manager)
    # ------------------------------------------------------------------

    @staticmethod
    def play(urgent=False):
        play_notification_sound(urgent)

    @staticmethod
    def play_critical():
        for _ in range(3):
            play_notification_sound(urgent=True)

    # ------------------------------------------------------------------
    # Timer
    # ------------------------------------------------------------------

    def _timer_tick(self):
        """Periodic check loop – runs every CHECK_INTERVAL_MS."""
        if not self._running:
            return
        try:
            self.power_monitor.check()
            self._check_midnight_reset()
            self._update_tray_state()

            if self.config.get("reminders_enabled", True):
                sch = self.schedule_manager.get_schedule(
                    self.config.is_dst_active())
                if not sch["no_reminders"]:
                    self._check_login_reminder(sch)
                    self._check_logout_reminder(sch)
                    self._check_work_prep_reminder(sch)
        except Exception as e:
            logging.exception("Timer tick error: %s", e)
        finally:
            self.root.after(CHECK_INTERVAL_MS, self._timer_tick)

    # ------------------------------------------------------------------
    # Daily state persistence (survives restarts)
    # ------------------------------------------------------------------

    def _restore_daily_state(self):
        ds = self.config.get("daily_state")
        if ds and ds.get("date") == datetime.now().strftime("%Y-%m-%d"):
            self.state["login_acknowledged"] = ds.get("login_acknowledged", False)
            self.state["logout_acknowledged"] = ds.get("logout_acknowledged", False)
            self.state["work_prep_acknowledged"] = ds.get("work_prep_acknowledged", False)
            logging.info("Restored daily state: login=%s, logout=%s, work_prep=%s",
                          self.state["login_acknowledged"],
                          self.state["logout_acknowledged"],
                          self.state["work_prep_acknowledged"])
        self._update_tray_state()

    def _save_daily_state(self):
        self.config.set("daily_state", {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "login_acknowledged": self.state["login_acknowledged"],
            "logout_acknowledged": self.state["logout_acknowledged"],
            "work_prep_acknowledged": self.state["work_prep_acknowledged"],
        })
        self.config.save()

    def _clear_daily_state(self):
        self.config.set("daily_state", None)
        self.config.save()

    # ------------------------------------------------------------------
    # Midnight reset & daily summary
    # ------------------------------------------------------------------

    def _check_midnight_reset(self):
        if self.daily_summary.is_new_day():
            summary = self.daily_summary.generate_summary()
            logging.info(summary)
            self.daily_summary.reset()
            self.state["login_acknowledged"] = False
            self.state["logout_acknowledged"] = False
            self.state["work_prep_acknowledged"] = False
            self.state["login_reminder_first_shown"] = None
            self.state["logout_reminder_first_shown"] = None
            self._login_snooze_until = None
            self._logout_snooze_until = None
            self._work_prep_popup = None
            self._work_prep_snooze_until = None
            self._clear_daily_state()
            logging.info("Daily state reset at midnight")

    # ------------------------------------------------------------------
    # Login reminder logic
    # ------------------------------------------------------------------

    def _is_past_login_time(self):
        dst = self.config.is_dst_active()
        return self.schedule_manager.is_time_past(
            self.schedule_manager.get_schedule(dst)["login_time"])

    def _is_past_logout_time(self):
        dst = self.config.is_dst_active()
        return self.schedule_manager.is_time_past(
            self.schedule_manager.get_schedule(dst)["logout_time"])

    def _is_within_login_unlock_window(self):
        dst = self.config.is_dst_active()
        sch = self.schedule_manager.get_schedule(dst)
        if sch["no_reminders"] or not sch["login_required"]:
            return False
        return self.schedule_manager.is_time_in_range(
            sch["login_unlock_start"], sch["login_unlock_end"])

    def _is_within_logout_unlock_window(self):
        dst = self.config.is_dst_active()
        sch = self.schedule_manager.get_schedule(dst)
        if sch["no_reminders"] or not sch["logout_required"]:
            return False
        return self.schedule_manager.is_time_in_range(
            sch["logout_unlock_start"], sch["logout_unlock_end"])

    def _get_next_reminder_time(self):
        dst = self.config.is_dst_active()
        sch = self.schedule_manager.get_schedule(dst)
        now = datetime.now()
        candidates = []
        if sch["login_required"] and not self.state["login_acknowledged"]:
            t = datetime.combine(now.date(), sch["login_time"])
            if t > now:
                candidates.append(t)
        if sch["logout_required"] and not self.state["logout_acknowledged"]:
            t = datetime.combine(now.date(), sch["logout_time"])
            if t > now:
                candidates.append(t)
        return min(candidates) if candidates else None

    # ------------------------------------------------------------------
    # Reminder checks (called from timer tick)
    # ------------------------------------------------------------------

    def _check_login_reminder(self, sch):
        if not sch["login_required"] or self.state["login_acknowledged"]:
            return
        if not self.schedule_manager.is_time_past(sch["login_time"]):
            return
        if self._login_snooze_until and datetime.now() < self._login_snooze_until:
            return
        if self._login_popup or self._critical_login_popup:
            return

        # Decide: normal popup or critical
        if self.schedule_manager.is_time_past(sch["login_critical_time"]):
            self._show_critical_login()
        else:
            self._show_login_reminder()

    def _check_logout_reminder(self, sch):
        if not sch["logout_required"] or self.state["logout_acknowledged"]:
            return
        if not self.schedule_manager.is_time_past(sch["logout_time"]):
            return
        if self._logout_snooze_until and datetime.now() < self._logout_snooze_until:
            return
        if self._logout_popup or self._critical_logout_popup:
            return

        # Decide: normal popup or critical escalation
        first = self.state["logout_reminder_first_shown"]
        if first:
            elapsed = (datetime.now() - first).total_seconds() / 60
            if elapsed >= 60:
                self._show_critical_logout()
                return

        self._show_logout_reminder()

    # ------------------------------------------------------------------
    # Work preparation reminder (only if login acknowledged)
    # ------------------------------------------------------------------

    def _check_work_prep_reminder(self, sch):
        if not sch["login_required"] or not self.state["login_acknowledged"]:
            return
        if self.state["work_prep_acknowledged"]:
            logging.debug("[WORK_PREP] Skipped - already acknowledged")
            return
        if not self.schedule_manager.is_time_past(sch["work_prep_time"]):
            return
        if self.schedule_manager.is_time_past(sch["shift_start"]):
            return
        if self._work_prep_snooze_until and datetime.now() < self._work_prep_snooze_until:
            return
        if self._work_prep_popup:
            return
        self._show_work_prep_reminder()

    def _show_work_prep_reminder(self):
        logging.info("[WORK_PREP] Shown")
        self.play()
        self._work_prep_popup = PopupWindow(
            self.root, "work_preparation",
            self._on_reminder_done, self._on_reminder_snooze)

    # ------------------------------------------------------------------
    # Show reminders
    # ------------------------------------------------------------------

    def _show_login_reminder(self):
        if self.state["login_acknowledged"]:
            return
        logging.info("Login reminder shown")
        if self.state["login_reminder_first_shown"] is None:
            self.state["login_reminder_first_shown"] = datetime.now()
        self.daily_summary.log_login_reminder()
        self.play()
        self._login_popup = PopupWindow(
            self.root, "login",
            self._on_reminder_done, self._on_reminder_snooze)

    def _show_logout_reminder(self):
        if self.state["logout_acknowledged"]:
            return
        logging.info("Logout reminder shown")
        if self.state["logout_reminder_first_shown"] is None:
            self.state["logout_reminder_first_shown"] = datetime.now()
        self.daily_summary.log_logout_reminder()

        first = self.state["logout_reminder_first_shown"]
        elapsed = (datetime.now() - first).total_seconds() / 60 if first else 0

        urgent = elapsed >= 15
        self.play(urgent=urgent)

        self._logout_popup = PopupWindow(
            self.root, "logout",
            self._on_reminder_done, self._on_reminder_snooze)

        if elapsed >= 30:
            from .utils import get_window_hwnd, flash_taskbar_window
            hwnd = get_window_hwnd(self._logout_popup)
            if hwnd:
                flash_taskbar_window(hwnd)

    def _show_critical_login(self):
        logging.info("Critical login warning shown")
        self.play_critical()
        self._critical_login_popup = CriticalWindow(
            self.root, "login",
            self._on_reminder_done, self._on_reminder_snooze)

    def _show_critical_logout(self):
        logging.info("Critical logout warning shown")
        self.play_critical()
        self._critical_logout_popup = CriticalWindow(
            self.root, "logout",
            self._on_reminder_done, self._on_reminder_snooze)

    # ------------------------------------------------------------------
    # Reminder callbacks
    # ------------------------------------------------------------------

    def _on_reminder_done(self, reminder_type):
        if reminder_type == "login":
            self.state["login_acknowledged"] = True
            self.daily_summary.log_login_confirmed()
            self._login_popup = None
            self._critical_login_popup = None
            self._login_snooze_until = None
            logging.info("Login confirmed by user")
            self._save_daily_state()
        elif reminder_type == "logout":
            self.state["logout_acknowledged"] = True
            self.daily_summary.log_logout_confirmed()
            self._logout_popup = None
            self._critical_logout_popup = None
            self._logout_snooze_until = None
            logging.info("Logout confirmed by user")
            self._save_daily_state()
        elif reminder_type == "work_preparation":
            self.state["work_prep_acknowledged"] = True
            self._work_prep_popup = None
            self._work_prep_snooze_until = None
            logging.info("[WORK_PREP] Acknowledged")
            self._save_daily_state()
        self._update_tray_state()

    def _on_reminder_snooze(self, reminder_type, critical_reshow=False):
        if reminder_type == "work_preparation":
            snooze = timedelta(seconds=CRITICAL_RESHOW_SEC)
        elif critical_reshow:
            snooze = timedelta(seconds=CRITICAL_RESHOW_SEC)
        else:
            snooze = timedelta(minutes=self.config.get("snooze_minutes",
                                                        SNOOZE_DEFAULT_MIN))

        until = datetime.now() + snooze

        if reminder_type == "login":
            self._login_snooze_until = until
            self._login_popup = None
            self._critical_login_popup = None
            logging.info("Login snoozed until %s",
                         until.strftime("%Y-%m-%d %I:%M:%S %p"))
        elif reminder_type == "logout":
            self._logout_snooze_until = until
            self._logout_popup = None
            self._critical_logout_popup = None
            logging.info("Logout snoozed until %s",
                         until.strftime("%Y-%m-%d %I:%M:%S %p"))
        elif reminder_type == "work_preparation":
            self._work_prep_snooze_until = until
            self._work_prep_popup = None
            logging.info("[WORK_PREP] Snoozed 60s")
        self._update_tray_state()

    # ------------------------------------------------------------------
    # Unlock / wake events
    # ------------------------------------------------------------------

    def _on_unlock(self):
        logging.info("Workstation unlock detected")
        if not self.config.get("reminders_enabled", True):
            return
        if self._is_within_login_unlock_window():
            if not self.state["login_acknowledged"]:
                self._login_snooze_until = None
            self.root.after(500, self._check_reminders_now)
        if (self._is_within_logout_unlock_window()
                and not self.state["logout_acknowledged"]):
            self._logout_snooze_until = None
            self.root.after(500, self._check_reminders_now)

    def _on_wake(self):
        logging.info("Wake from sleep detected")
        if not self.config.get("reminders_enabled", True):
            return
        self._login_snooze_until = None
        self._logout_snooze_until = None
        self._work_prep_snooze_until = None
        self.root.after(1000, self._check_reminders_now)

    def _check_reminders_now(self):
        try:
            sch = self.schedule_manager.get_schedule(
                self.config.is_dst_active())
            if not sch["no_reminders"]:
                self._check_login_reminder(sch)
                self._check_logout_reminder(sch)
                self._check_work_prep_reminder(sch)
            self._update_tray_state()
        except Exception as e:
            logging.exception("Check reminders error: %s", e)

    # ------------------------------------------------------------------
    # Tray state
    # ------------------------------------------------------------------

    def _update_tray_state(self):
        try:
            sch = self.schedule_manager.get_schedule(
                self.config.is_dst_active())
            st = self.state
            login_overdue = (sch["login_required"] and not st["login_acknowledged"]
                             and self._is_past_login_time())
            logout_overdue = (sch["logout_required"] and not st["logout_acknowledged"]
                              and self._is_past_logout_time())

            if sch["no_reminders"]:
                self.tray.set_color(ICON_GREEN)
            elif (login_overdue and self._is_critical_passed("login")) or \
                 (logout_overdue and self._is_logout_escalated()):
                self.tray.set_color(ICON_RED)
            elif login_overdue or logout_overdue:
                self.tray.set_color(ICON_YELLOW)
            else:
                self.tray.set_color(ICON_GREEN)
            self.tray.update_tooltip()
        except Exception:
            pass

    def _is_critical_passed(self, rtype):
        dst = self.config.is_dst_active()
        sch = self.schedule_manager.get_schedule(dst)
        t = sch.get("login_critical_time") if rtype == "login" else None
        return t and self.schedule_manager.is_time_past(t)

    def _is_logout_escalated(self):
        first = self.state["logout_reminder_first_shown"]
        if first:
            return (datetime.now() - first).total_seconds() / 60 >= 60
        return False

    # ------------------------------------------------------------------
    # Settings / Dashboard
    # ------------------------------------------------------------------

    def on_settings_changed(self):
        logging.info("Settings updated, reapplying configuration")
        set_auto_start(self.config.get("auto_start", False))
        self._update_tray_state()

    def show_dashboard(self):
        if self.dashboard_window and self.dashboard_window.winfo_exists():
            self.dashboard_window.lift()
            self.dashboard_window.focus_force()
            return
        self.dashboard_window = DashboardWindow(self.root, self)
        self.dashboard_window.refresh()

    def show_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return
        self.settings_window = SettingsWindow(self.root, self)

    def test_reminder(self, reminder_type):
        logging.info("Test %s reminder triggered by user", reminder_type)
        self._login_snooze_until = None
        self._logout_snooze_until = None
        PopupWindow(
            self.root, reminder_type,
            on_done=lambda rt: logging.info("Test %s dismissed", rt),
            on_snooze=lambda rt, cr: logging.info("Test %s snoozed", rt),
        )

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    def shutdown(self):
        if not self._running:
            return
        self._running = False
        logging.info("Application shutting down")
        self.session_monitor.stop()
        self.tray.stop()
        self.config.save()
        logging.info("%s", "=" * 50)
        logging.info("  %s Stopped", APP_NAME)
        logging.info("%s", "=" * 50)
        self.root.quit()

    def _on_root_close(self):
        self.root.withdraw()

    def _log_initial_state(self):
        sch = self.schedule_manager.get_schedule(
            self.config.is_dst_active())
        logging.debug("Today: %s", datetime.now().strftime("%A"))
        logging.debug("Login required: %s", sch["login_required"])
        logging.debug("Logout required: %s", sch["logout_required"])
        logging.debug("No reminders: %s", sch["no_reminders"])
