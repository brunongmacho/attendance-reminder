"""
User interface components for Attendance Reminder.

Provides Tkinter-based windows:
  - PopupWindow: standard reminder with Done / Remind Me Again
  - CriticalWindow: large red urgent warning that aggressively reappears
  - DashboardWindow: today's status overview with test buttons
  - SettingsWindow: full settings editor with import/export/backup
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import shutil
import logging

from .utils import (
    APP_NAME, TIME_FORMAT, DATETIME_FORMAT, CRITICAL_RESHOW_SEC,
    flash_taskbar_window, get_window_hwnd, play_notification_sound,
    set_auto_start, is_auto_start_enabled,
)


# ---------------------------------------------------------------------------
# Reminder Popup  (login / logout)
# ---------------------------------------------------------------------------

class PopupWindow(tk.Toplevel):
    """Standard reminder with checkbox + Done/Remind Me Again buttons."""

    def __init__(self, parent, reminder_type, on_done, on_snooze):
        super().__init__(parent)
        self.reminder_type = reminder_type
        self._on_done_cb = on_done
        self._on_snooze_cb = on_snooze
        self._acknowledged = False

        self.title("Attendance Reminder")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._center()
        self.focus_force()
        self.grab_set()
    def _build_ui(self):
        f = ttk.Frame(self, padding=20)
        f.pack(fill=tk.BOTH, expand=True)

        if self.reminder_type == "work_preparation":
            msg = "Your shift begins in 5 minutes."
            detail = ("Please open your work applications, prepare your "
                      "workstation, and get ready to start work.")
            chk_text = "I have prepared my workstation."
        elif self.reminder_type == "login":
            msg = "Time to log in to the attendance system!"
            detail = "Please confirm your attendance login."
            chk_text = "I have already logged in/out of the attendance system."
        else:
            msg = "Time to log out of the attendance system!"
            detail = "Please confirm your attendance logout."
            chk_text = "I have already logged in/out of the attendance system."

        ttk.Label(f, text=msg, font=("Segoe UI", 14, "bold"),
                  wraplength=380).pack(pady=(0, 5))
        ttk.Label(f, text=detail, font=("Segoe UI", 10),
                  wraplength=380).pack(pady=(0, 10))

        ttk.Label(f, text=f"Current Time: {datetime.now().strftime(TIME_FORMAT)}",
                  font=("Segoe UI", 9), foreground="gray").pack(pady=(0, 15))

        self._check_var = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(
            f,
            text=chk_text,
            variable=self._check_var,
            command=self._on_check_changed,
        )
        chk.pack(pady=(0, 15), anchor=tk.W)

        bf = ttk.Frame(f)
        bf.pack(fill=tk.X)
        self._done_btn = ttk.Button(bf, text="Done",
                                    command=self._on_done, state=tk.DISABLED)
        self._done_btn.pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(bf, text="Remind Me Again",
                   command=self._on_snooze).pack(side=tk.RIGHT)
        self.minsize(400, 220)

    def _center(self):
        self.update_idletasks()
        w = max(400, self.winfo_reqwidth())
        h = max(220, self.winfo_reqheight())
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _on_check_changed(self):
        self._done_btn.config(state=tk.NORMAL if self._check_var.get() else tk.DISABLED)

    def _on_done(self):
        self._acknowledged = True
        if self._on_done_cb:
            self._on_done_cb(self.reminder_type)
        self.destroy()

    def _on_snooze(self):
        if self._on_snooze_cb:
            self._on_snooze_cb(self.reminder_type, False)
        self.destroy()

    def _on_close(self):
        if not self._acknowledged:
            self._on_snooze()
        else:
            self.destroy()


# ---------------------------------------------------------------------------
# Critical Warning  (large red urgent window)
# ---------------------------------------------------------------------------

class CriticalWindow(tk.Toplevel):
    """Large red critical warning that flashes taskbar and re-shows on close."""

    def __init__(self, parent, reminder_type, on_done, on_snooze):
        super().__init__(parent)
        self.reminder_type = reminder_type
        self._on_done_cb = on_done
        self._on_snooze_cb = on_snooze
        self._acknowledged = False

        self.title("ATTENTION REQUIRED")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._center()
        self.focus_force()
        self.grab_set_global()

        hwnd = get_window_hwnd(self)
        if hwnd:
            flash_taskbar_window(hwnd)

    def _build_ui(self):
        self.configure(bg="#8B0000")
        f = tk.Frame(self, bg="#8B0000", padx=30, pady=20)
        f.pack(fill=tk.BOTH, expand=True)

        if self.reminder_type == "login":
            title_t = "URGENT"
            detail_t = ("You have not confirmed attendance login.\n\n"
                        "Your shift begins in 10 minutes.")
        else:
            title_t = "REMINDER:"
            detail_t = "YOU HAVE NOT CONFIRMED YOUR ATTENDANCE LOGOUT."

        tk.Label(f, text=title_t, font=("Segoe UI", 20, "bold"),
                 fg="white", bg="#8B0000", wraplength=540).pack(pady=(0, 10))
        tk.Label(f, text=detail_t, font=("Segoe UI", 14, "bold"),
                 fg="white", bg="#8B0000", wraplength=540).pack(pady=(0, 15))
        tk.Label(f, text=f"Current Time: {datetime.now().strftime(TIME_FORMAT)}",
                 font=("Segoe UI", 11), fg="#FFCCCC",
                 bg="#8B0000").pack(pady=(0, 20))

        self._check_var = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(f, fg="white", bg="#8B0000",
                             selectcolor="#8B0000", font=("Segoe UI", 10),
                             text="I have already logged in/out of the attendance system.",
                             variable=self._check_var,
                             command=self._on_check_changed)
        chk.pack(pady=(0, 15), anchor=tk.W)

        bf = tk.Frame(f, bg="#8B0000")
        bf.pack(fill=tk.X)
        self._done_btn = tk.Button(bf, text="Done",
                                   command=self._on_done, state=tk.DISABLED,
                                   bg="#FF4444", fg="white",
                                   font=("Segoe UI", 11, "bold"),
                                   padx=20, pady=5, relief=tk.RAISED, bd=2)
        self._done_btn.pack(side=tk.RIGHT, padx=(5, 0))
        tk.Button(bf, text="Remind Me Again",
                  command=self._on_snooze,
                  bg="#CC0000", fg="white", font=("Segoe UI", 11),
                  padx=15, pady=5, relief=tk.RAISED, bd=2).pack(side=tk.RIGHT)
        self.minsize(540, 260)

    def _center(self):
        self.update_idletasks()
        w = max(540, self.winfo_reqwidth())
        h = max(260, self.winfo_reqheight())
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _on_check_changed(self):
        self._done_btn.config(state=tk.NORMAL if self._check_var.get() else tk.DISABLED)

    def _on_done(self):
        self._acknowledged = True
        if self._on_done_cb:
            self._on_done_cb(self.reminder_type)
        self.destroy()

    def _on_snooze(self):
        if self._on_snooze_cb:
            self._on_snooze_cb(self.reminder_type, True)
        self.destroy()

    def _on_close(self):
        if not self._acknowledged:
            self._on_snooze()
        else:
            self.destroy()


# ---------------------------------------------------------------------------
# Attendance Recovery Mode
# ---------------------------------------------------------------------------

class AttendanceRecoveryWindow(tk.Toplevel):
    """Checklist modal for recovering from suspected missed attendance."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("Attendance Recovery Checklist")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._build_ui()
        self._center()
        self.focus_force()
        self.grab_set()

    def _build_ui(self):
        m = ttk.Frame(self, padding=15)
        m.pack(fill=tk.BOTH, expand=True)

        ttk.Label(m, text="Attendance Recovery Checklist",
                  font=("Segoe UI", 13, "bold")).pack(pady=(0, 10))

        self._checklist_items = [
            "Step 1: Verify attendance website status.",
            "Step 2: Verify current attendance record.",
            "Step 3: Check whether login or logout was completed.",
            "Step 4: Determine if a Certificate of Attendance (COA) is required.",
            "Step 5: File COA if needed.",
            "Step 6: Document reason.",
        ]

        self._check_vars = []
        for item in self._checklist_items:
            var = tk.BooleanVar(value=False)
            self._check_vars.append(var)
            ttk.Checkbutton(m, text=item, variable=var).pack(
                anchor=tk.W, pady=2, padx=10)

        bf = ttk.Frame(m)
        bf.pack(fill=tk.X, pady=(15, 0))
        ttk.Button(bf, text="Close",
                   command=self.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(bf, text="Copy Checklist",
                   command=self._copy_checklist).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(bf, text="Open Log File",
                   command=self._open_logs).pack(side=tk.RIGHT)

    def _center(self):
        self.update_idletasks()
        w = self.winfo_reqwidth() + 20
        h = self.winfo_reqheight() + 20
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _copy_checklist(self):
        text = "Attendance Recovery Checklist\n"
        text += "=" * 35 + "\n"
        for i, item in enumerate(self._checklist_items):
            done = "✓" if self._check_vars[i].get() else "○"
            text += f"{done} {item}\n"
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", "Checklist copied to clipboard.")

    def _open_logs(self):
        try:
            os.startfile(str(self.app.app_dir / "attendance_reminder.log"))
        except Exception:
            messagebox.showerror("Error", "Failed to open log file.")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class DashboardWindow(tk.Toplevel):
    """Shows shift times, reminder times, attendance summary, and actions."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title(f"{APP_NAME} - Dashboard")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._center()

    def _build_ui(self):
        m = ttk.Frame(self, padding=15)
        m.pack(fill=tk.BOTH, expand=True)
        ttk.Label(m, text=APP_NAME,
                  font=("Segoe UI", 16, "bold")).pack(pady=(0, 10))

        # ---- Shift Times ----
        sf = ttk.LabelFrame(m, text="Shift Times", padding=10)
        sf.pack(fill=tk.X, pady=5)
        self._shift_start_lbl = ttk.Label(sf, text="", font=("Segoe UI", 10))
        self._shift_start_lbl.pack(anchor=tk.W, pady=1)
        self._shift_end_lbl = ttk.Label(sf, text="", font=("Segoe UI", 10))
        self._shift_end_lbl.pack(anchor=tk.W, pady=1)

        # ---- Reminder Times ----
        rf = ttk.LabelFrame(m, text="Reminder Times", padding=10)
        rf.pack(fill=tk.X, pady=5)
        self._reminder_login_lbl = ttk.Label(rf, text="", font=("Segoe UI", 10))
        self._reminder_login_lbl.pack(anchor=tk.W, pady=1)
        self._reminder_critical_lbl = ttk.Label(rf, text="", font=("Segoe UI", 10))
        self._reminder_critical_lbl.pack(anchor=tk.W, pady=1)
        self._reminder_work_prep_lbl = ttk.Label(rf, text="", font=("Segoe UI", 10))
        self._reminder_work_prep_lbl.pack(anchor=tk.W, pady=1)
        self._reminder_logout_lbl = ttk.Label(rf, text="", font=("Segoe UI", 10))
        self._reminder_logout_lbl.pack(anchor=tk.W, pady=1)

        # ---- Today's Attendance Summary ----
        af = ttk.LabelFrame(m, text="Today's Attendance Summary", padding=10)
        af.pack(fill=tk.X, pady=5)
        self._mode_lbl = ttk.Label(af, text="", font=("Segoe UI", 10))
        self._mode_lbl.pack(anchor=tk.W, pady=1)
        self._login_status_lbl = ttk.Label(af, text="", font=("Segoe UI", 10))
        self._login_status_lbl.pack(anchor=tk.W, pady=1)
        self._login_time_lbl = ttk.Label(af, text="", font=("Segoe UI", 10))
        self._login_time_lbl.pack(anchor=tk.W, pady=1)
        self._logout_status_lbl = ttk.Label(af, text="", font=("Segoe UI", 10))
        self._logout_status_lbl.pack(anchor=tk.W, pady=1)
        self._logout_time_lbl = ttk.Label(af, text="", font=("Segoe UI", 10))
        self._logout_time_lbl.pack(anchor=tk.W, pady=1)
        self._last_reminder_lbl = ttk.Label(af, text="", font=("Segoe UI", 10))
        self._last_reminder_lbl.pack(anchor=tk.W, pady=1)

        # ---- Actions ----
        bf = ttk.LabelFrame(m, text="Actions", padding=10)
        bf.pack(fill=tk.X, pady=5)
        ttk.Button(bf, text="Test Login Reminder",
                   command=lambda: self.app.test_reminder("login")).pack(fill=tk.X, pady=2)
        ttk.Button(bf, text="Test Logout Reminder",
                   command=lambda: self.app.test_reminder("logout")).pack(fill=tk.X, pady=2)
        ttk.Button(bf, text="View Logs",
                   command=self._view_logs).pack(fill=tk.X, pady=2)
        ttk.Button(bf, text="Settings",
                   command=self.app.show_settings).pack(fill=tk.X, pady=2)
        ttk.Button(bf, text=chr(9888) + " Attendance Recovery",
                   command=self._open_recovery).pack(fill=tk.X, pady=2)

        ttk.Button(m, text="Refresh",
                   command=self.refresh).pack(pady=(10, 0))

    def _center(self):
        self.update_idletasks()
        w = self.winfo_reqwidth() + 20
        h = self.winfo_reqheight() + 20
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def refresh(self):
        """Update all displayed fields from the app state."""
        try:
            sch = self.app.schedule_manager.get_schedule(
                self.app.config.is_dst_active())
            st = self.app.state
            ds = self.app.daily_summary

            self._mode_lbl.config(text=f"Current Mode: {sch['mode_name']}")

            # Shift Times
            self._shift_start_lbl.config(
                text=f"Shift Start: {sch['shift_start'].strftime(TIME_FORMAT)}")
            self._shift_end_lbl.config(
                text=f"Shift End: {sch['shift_end'].strftime(TIME_FORMAT)}")

            # Reminder Times
            self._reminder_login_lbl.config(
                text=f"Login Reminder: {sch['login_time'].strftime(TIME_FORMAT)}")
            self._reminder_critical_lbl.config(
                text=f"Login Critical: {sch['login_critical_time'].strftime(TIME_FORMAT)}")
            wp = sch.get("work_prep_time")
            self._reminder_work_prep_lbl.config(
                text=f"Work Preparation: {wp.strftime(TIME_FORMAT) if wp else 'N/A'}")
            self._reminder_logout_lbl.config(
                text=f"Logout Reminder: {sch['logout_time'].strftime(TIME_FORMAT)}")

            # Login Status
            if st["login_acknowledged"]:
                t = ds.login_confirmed
                ls = f"Completed ({t.strftime(TIME_FORMAT)})" if t else "Completed"
                lt = f"Login Confirmation: {t.strftime(TIME_FORMAT)}" if t else ""
            elif sch["login_required"] and self.app._is_past_login_time():
                ls = "Overdue"
                lt = ""
            elif sch["login_required"]:
                ls = "Pending"
                lt = ""
            else:
                ls = "Not Required"
                lt = ""
            self._login_status_lbl.config(text=f"Login Status: {ls}")
            self._login_time_lbl.config(text=lt)

            # Logout Status
            if st["logout_acknowledged"]:
                t = ds.logout_confirmed
                os_ = f"Completed ({t.strftime(TIME_FORMAT)})" if t else "Completed"
                ot = f"Logout Confirmation: {t.strftime(TIME_FORMAT)}" if t else ""
            elif sch["logout_required"] and self.app._is_past_logout_time():
                os_ = "Overdue"
                ot = ""
            elif sch["logout_required"]:
                os_ = "Pending"
                ot = ""
            else:
                os_ = "Not Required"
                ot = ""
            self._logout_status_lbl.config(text=f"Logout Status: {os_}")
            self._logout_time_lbl.config(text=ot)

            # Last reminder shown
            lr = ds.last_reminder_shown
            self._last_reminder_lbl.config(
                text=f"Last Reminder: {lr.strftime(TIME_FORMAT) if lr else 'None'}")

        except Exception as e:
            logging.error("Dashboard refresh error: %s", e)

    def _view_logs(self):
        try:
            os.startfile(str(self.app.app_dir / "attendance_reminder.log"))
        except Exception:
            messagebox.showerror("Error", "Failed to open log file.")

    def _open_recovery(self):
        AttendanceRecoveryWindow(self, self.app)

    def _on_close(self):
        self.app.dashboard_window = None
        self.destroy()


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class SettingsWindow(tk.Toplevel):
    """Full settings editor with schedule / general tabs and import/export."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.config = app.config
        self.title(f"{APP_NAME} - Settings")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self._vars = {}
        self._build_ui()
        self._load_values()
        self._center()

    def _build_ui(self):
        m = ttk.Frame(self, padding=15)
        m.pack(fill=tk.BOTH, expand=True)
        nb = ttk.Notebook(m)
        nb.pack(fill=tk.BOTH, expand=True, pady=5)

        # ---------- Schedule tab ----------
        sf = ttk.Frame(nb, padding=10)
        nb.add(sf, text="Schedule")

        r = 0
        ttk.Label(sf, text="Regular Schedule",
                  font=("Segoe UI", 10, "bold")).grid(
            row=r, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        r += 1

        for label, key in [
            ("Login Reminder:", "login"),
            ("Logout Reminder:", "logout"),
            ("Login Critical:", "login_critical"),
            ("Login Unlock Start:", "login_unlock_start"),
            ("Login Unlock End:", "login_unlock_end"),
            ("Logout Unlock Start:", "logout_unlock_start"),
            ("Logout Unlock End:", "logout_unlock_end"),
        ]:
            self._add_time(sf, r, label, key)
            r += 1

        r += 1
        ttk.Label(sf, text="DST Schedule",
                  font=("Segoe UI", 10, "bold")).grid(
            row=r, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        r += 1

        for label, key in [
            ("DST Login Reminder:", "dst_login"),
            ("DST Logout Reminder:", "dst_logout"),
            ("DST Login Critical:", "dst_login_critical"),
            ("DST Login Unlock Start:", "dst_login_unlock_start"),
            ("DST Login Unlock End:", "dst_login_unlock_end"),
            ("DST Logout Unlock Start:", "dst_logout_unlock_start"),
            ("DST Logout Unlock End:", "dst_logout_unlock_end"),
        ]:
            self._add_time(sf, r, label, key)
            r += 1

        # ---------- General tab ----------
        gf = ttk.Frame(nb, padding=10)
        nb.add(gf, text="General")

        r = 0
        self._vars["snooze_minutes"] = tk.IntVar(value=5)
        ttk.Label(gf, text="Snooze Duration (minutes):").grid(
            row=r, column=0, sticky=tk.W, pady=3)
        ttk.Spinbox(gf, from_=1, to=60,
                     textvariable=self._vars["snooze_minutes"],
                     width=5).grid(row=r, column=1, sticky=tk.W, pady=3)
        r += 1

        self._vars["reminders_enabled"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(gf, text="Enable Reminders",
                         variable=self._vars["reminders_enabled"]).grid(
            row=r, column=0, columnspan=2, sticky=tk.W, pady=3)
        r += 1

        self._vars["auto_start"] = tk.BooleanVar(value=False)
        ttk.Checkbutton(gf, text="Start with Windows",
                         variable=self._vars["auto_start"]).grid(
            row=r, column=0, columnspan=2, sticky=tk.W, pady=3)
        r += 1

        self._vars["sound_enabled"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(gf, text="Enable Sound",
                         variable=self._vars["sound_enabled"]).grid(
            row=r, column=0, columnspan=2, sticky=tk.W, pady=3)
        r += 1

        self._vars["dst_auto_detect"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(gf, text="Auto-Detect DST",
                         variable=self._vars["dst_auto_detect"]).grid(
            row=r, column=0, columnspan=2, sticky=tk.W, pady=3)
        r += 1

        self._vars["dst_override"] = tk.StringVar(value="auto")
        ovf = ttk.Frame(gf)
        ovf.grid(row=r, column=0, columnspan=2, sticky=tk.W, pady=3)
        ttk.Label(ovf, text="DST Override:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Radiobutton(ovf, text="Auto", variable=self._vars["dst_override"],
                         value="auto").pack(side=tk.LEFT)
        ttk.Radiobutton(ovf, text="Regular",
                         variable=self._vars["dst_override"],
                         value="regular").pack(side=tk.LEFT)
        ttk.Radiobutton(ovf, text="DST", variable=self._vars["dst_override"],
                         value="dst").pack(side=tk.LEFT)

        # ---------- Buttons ----------
        bf = ttk.Frame(m)
        bf.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(bf, text="Save", command=self._on_save).pack(
            side=tk.RIGHT, padx=(5, 0))
        ttk.Button(bf, text="Cancel", command=self._on_cancel).pack(
            side=tk.RIGHT)
        ttk.Button(bf, text="Import", command=self._on_import).pack(
            side=tk.LEFT, padx=(0, 5))
        ttk.Button(bf, text="Export", command=self._on_export).pack(
            side=tk.LEFT)
        ttk.Button(bf, text="Backup", command=self._on_backup).pack(
            side=tk.LEFT, padx=(5, 0))

    # ---- helpers ----

    def _add_time(self, parent, row, label, key):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
        h_var = tk.StringVar(value="00")
        m_var = tk.StringVar(value="00")
        self._vars[f"{key}_hour"] = h_var
        self._vars[f"{key}_minute"] = m_var
        pf = ttk.Frame(parent)
        pf.grid(row=row, column=1, sticky=tk.W, pady=2)
        ttk.Combobox(pf, textvariable=h_var,
                      values=[f"{h:02d}" for h in range(24)],
                      width=3, state="readonly").pack(side=tk.LEFT)
        ttk.Label(pf, text=":").pack(side=tk.LEFT)
        ttk.Combobox(pf, textvariable=m_var,
                      values=[f"{m:02d}" for m in range(60)],
                      width=3, state="readonly").pack(side=tk.LEFT)

    def _set_time(self, key, hour, minute):
        hk = f"{key}_hour"
        mk = f"{key}_minute"
        if hk in self._vars:
            self._vars[hk].set(f"{hour:02d}")
        if mk in self._vars:
            self._vars[mk].set(f"{minute:02d}")

    def _get_time(self, key):
        h = int(self._vars.get(f"{key}_hour", tk.StringVar(value="0")).get())
        m = int(self._vars.get(f"{key}_minute", tk.StringVar(value="0")).get())
        return h, m

    def _load_values(self):
        cfg = self.config.settings
        pairs = [
            ("login", "login_hour", "login_minute"),
            ("logout", "logout_hour", "logout_minute"),
            ("login_critical", "login_critical_hour", "login_critical_minute"),
            ("login_unlock_start", "login_unlock_start_hour", "login_unlock_start_minute"),
            ("login_unlock_end", "login_unlock_end_hour", "login_unlock_end_minute"),
            ("logout_unlock_start", "logout_unlock_start_hour", "logout_unlock_start_minute"),
            ("logout_unlock_end", "logout_unlock_end_hour", "logout_unlock_end_minute"),
            ("dst_login", "dst_login_hour", "dst_login_minute"),
            ("dst_logout", "dst_logout_hour", "dst_logout_minute"),
            ("dst_login_critical", "dst_login_critical_hour", "dst_login_critical_minute"),
            ("dst_login_unlock_start", "dst_login_unlock_start_hour", "dst_login_unlock_start_minute"),
            ("dst_login_unlock_end", "dst_login_unlock_end_hour", "dst_login_unlock_end_minute"),
            ("dst_logout_unlock_start", "dst_logout_unlock_start_hour", "dst_logout_unlock_start_minute"),
            ("dst_logout_unlock_end", "dst_logout_unlock_end_hour", "dst_logout_unlock_end_minute"),
        ]
        for key, hk, mk in pairs:
            self._set_time(key, cfg.get(hk, 0), cfg.get(mk, 0))

        self._vars["snooze_minutes"].set(cfg.get("snooze_minutes", 5))
        self._vars["reminders_enabled"].set(cfg.get("reminders_enabled", True))
        self._vars["auto_start"].set(is_auto_start_enabled())
        self._vars["sound_enabled"].set(cfg.get("sound_enabled", True))
        self._vars["dst_auto_detect"].set(cfg.get("dst_auto_detect", True))

        ov = cfg.get("dst_override")
        if ov is None:
            self._vars["dst_override"].set("auto")
        elif ov:
            self._vars["dst_override"].set("dst")
        else:
            self._vars["dst_override"].set("regular")

    def _center(self):
        self.update_idletasks()
        w = self.winfo_reqwidth() + 20
        h = self.winfo_reqheight() + 20
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _on_save(self):
        try:
            cfg = self.config.settings
            mappings = [
                ("login", "login_hour", "login_minute"),
                ("logout", "logout_hour", "logout_minute"),
                ("login_critical", "login_critical_hour", "login_critical_minute"),
                ("login_unlock_start", "login_unlock_start_hour", "login_unlock_start_minute"),
                ("login_unlock_end", "login_unlock_end_hour", "login_unlock_end_minute"),
                ("logout_unlock_start", "logout_unlock_start_hour", "logout_unlock_start_minute"),
                ("logout_unlock_end", "logout_unlock_end_hour", "logout_unlock_end_minute"),
                ("dst_login", "dst_login_hour", "dst_login_minute"),
                ("dst_logout", "dst_logout_hour", "dst_logout_minute"),
                ("dst_login_critical", "dst_login_critical_hour", "dst_login_critical_minute"),
                ("dst_login_unlock_start", "dst_login_unlock_start_hour", "dst_login_unlock_start_minute"),
                ("dst_login_unlock_end", "dst_login_unlock_end_hour", "dst_login_unlock_end_minute"),
                ("dst_logout_unlock_start", "dst_logout_unlock_start_hour", "dst_logout_unlock_start_minute"),
                ("dst_logout_unlock_end", "dst_logout_unlock_end_hour", "dst_logout_unlock_end_minute"),
            ]
            for key, hk, mk in mappings:
                h, m = self._get_time(key)
                cfg[hk] = h
                cfg[mk] = m

            cfg["snooze_minutes"] = self._vars["snooze_minutes"].get()
            cfg["reminders_enabled"] = self._vars["reminders_enabled"].get()
            cfg["sound_enabled"] = self._vars["sound_enabled"].get()
            cfg["dst_auto_detect"] = self._vars["dst_auto_detect"].get()
            cfg["auto_start"] = self._vars["auto_start"].get()

            ov = self._vars["dst_override"].get()
            if ov == "auto":
                cfg["dst_override"] = None
            else:
                cfg["dst_override"] = (ov == "dst")

            self.config.save()
            set_auto_start(self._vars["auto_start"].get())
            self.app.on_settings_changed()
            self.destroy()
        except Exception as e:
            logging.exception("Failed to save settings")
            messagebox.showerror("Error", f"Failed to save settings:\n{e}")

    def _on_cancel(self):
        self.destroy()

    def _on_import(self):
        p = filedialog.askopenfilename(title="Import Settings",
                                        filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if p:
            try:
                self.config.import_settings(p)
                self._load_values()
                self.app.on_settings_changed()
                messagebox.showinfo("Success", "Settings imported.")
            except Exception as e:
                messagebox.showerror("Error", f"Import failed:\n{e}")

    def _on_export(self):
        p = filedialog.asksaveasfilename(title="Export Settings",
                                          defaultextension=".json",
                                          filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if p:
            try:
                self.config.export_settings(p)
                messagebox.showinfo("Success", "Settings exported.")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed:\n{e}")

    def _on_backup(self):
        try:
            shutil.copy2(self.config.settings_path, self.config.backup_path)
            messagebox.showinfo("Success", "Settings backed up.")
        except Exception as e:
            messagebox.showerror("Error", f"Backup failed:\n{e}")
