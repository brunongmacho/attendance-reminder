"""
System tray icon for Attendance Reminder.

Uses native win32gui + Shell_NotifyIcon instead of pystray to get reliable
left-click / double-click handling on Windows 11.
"""

import os
import time
import threading
import logging
import tempfile
import ctypes

import win32con
import win32gui
import win32api

from .utils import (
    APP_NAME, ICON_GREEN, ICON_YELLOW, ICON_RED, TIME_FORMAT,
    create_tray_icon_image, LOG_FILE,
)

# Custom window messages
WM_TRAY = win32con.WM_APP + 1
WM_UPDATE_ICON = win32con.WM_APP + 2
WM_UPDATE_TOOLTIP = win32con.WM_APP + 3
WM_STOP = win32con.WM_APP + 4

TRAY_ICON_ID = 1

# Menu command IDs
CMD_DASHBOARD = 1001
CMD_SETTINGS = 1002
CMD_TEST_LOGIN = 1003
CMD_TEST_LOGOUT = 1004
CMD_VIEW_LOGS = 1005
CMD_EXIT = 1006

_icon_counter = 0
_temp_dir = None


def _temp_ico_path():
    global _icon_counter, _temp_dir
    if _temp_dir is None:
        _temp_dir = tempfile.mkdtemp(prefix="att_reminder_")
    _icon_counter += 1
    return os.path.join(_temp_dir, f"icon_{_icon_counter}.ico")


def _pil_to_hicon(pil_image):
    """Convert a PIL RGBA image to a Windows HICON handle."""
    path = _temp_ico_path()
    pil_image.save(path, format="ICO", sizes=[(32, 32)])
    return win32gui.LoadImage(
        0, path, win32con.IMAGE_ICON, 32, 32,
        win32con.LR_LOADFROMFILE,
    )


# ---------------------------------------------------------------------------
# Tray manager – fully native Windows implementation
# ---------------------------------------------------------------------------

class TrayManager:
    """Native Windows system tray icon with reliable click handling."""

    def __init__(self, app):
        self.app = app
        self.hwnd = None
        self._running = False
        self._thread = None
        self.current_color = ICON_GREEN
        self._hicon = None

    # ---- public API called from any thread --------------------------------

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self.hwnd:
            win32gui.PostMessage(self.hwnd, WM_STOP, 0, 0)
        self._clear_icon()

    def set_color(self, color):
        if color != self.current_color:
            self.current_color = color
            if self.hwnd:
                win32gui.PostMessage(self.hwnd, WM_UPDATE_ICON, 0, 0)

    def update_tooltip(self):
        if self.hwnd:
            win32gui.PostMessage(self.hwnd, WM_UPDATE_TOOLTIP, 0, 0)

    # ---- background thread ------------------------------------------------

    def _run(self):
        module = win32api.GetModuleHandle(None)

        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self._wnd_proc
        wc.hInstance = module
        wc.lpszClassName = "AttendanceReminderTray_" + str(os.getpid())
        win32gui.RegisterClass(wc)

        self.hwnd = win32gui.CreateWindowEx(
            win32con.WS_EX_TOOLWINDOW,
            wc.lpszClassName, "Tray", win32con.WS_POPUP,
            0, 0, 0, 0, 0, 0, module, None,
        )

        logging.debug("Tray window created: hwnd=%d", self.hwnd)
        self._apply_icon()
        self._apply_tooltip()

        while self._running:
            win32gui.PumpWaitingMessages()
            time.sleep(0.05)

        self._clear_icon()
        win32gui.DestroyWindow(self.hwnd)
        self.hwnd = None

    # ---- window procedure (message loop thread) ---------------------------

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAY:
            if lparam == win32con.WM_LBUTTONUP:
                self.app.root.after(0, self.app.show_dashboard)
            elif lparam == win32con.WM_LBUTTONDBLCLK:
                self.app.root.after(0, self.app.show_dashboard)
            elif lparam in (win32con.WM_RBUTTONUP, win32con.WM_CONTEXTMENU):
                try:
                    self._show_context_menu()
                except Exception as e:
                    logging.exception("Context menu failed: %s", e)
            return 0

        if msg == WM_UPDATE_ICON:
            self._apply_icon()
            return 0

        if msg == WM_UPDATE_TOOLTIP:
            self._apply_tooltip()
            return 0

        if msg == WM_STOP:
            self._running = False
            return 0

        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    # ---- icon management --------------------------------------------------

    def _apply_icon(self):
        """Replace the tray icon with the current color (runs in msg thread)."""
        self._clear_icon()
        img = create_tray_icon_image(self.current_color)
        try:
            self._hicon = _pil_to_hicon(img)
        except Exception as e:
            logging.error("Failed to create tray icon: %s", e)
            return

        try:
            nid = (
                self.hwnd,
                TRAY_ICON_ID,
                win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                WM_TRAY,
                self._hicon,
                "Attendance Reminder",
            )
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
        except Exception as e:
            logging.error("Shell_NotifyIcon NIM_ADD failed: %s", e)

    def _apply_tooltip(self):
        """Update the tooltip text (runs in msg thread)."""
        tip = self._build_tooltip()
        try:
            nid = (
                self.hwnd,
                TRAY_ICON_ID,
                win32gui.NIF_TIP,
                0,
                0,
                tip[:127],
            )
            win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, nid)
        except Exception:
            pass

    def _clear_icon(self):
        if self._hicon:
            try:
                nid = (self.hwnd or 0, TRAY_ICON_ID, 0, 0, 0, "")
                win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
            except Exception:
                pass
            try:
                win32gui.DestroyIcon(self._hicon)
            except Exception:
                pass
            self._hicon = None

    # ---- context menu -----------------------------------------------------

    def _show_context_menu(self):
        logging.debug("Building context menu")
        hmenu = win32gui.CreatePopupMenu()
        items = [
            (CMD_DASHBOARD, "Dashboard"),
            (0, None),  # separator
            (CMD_SETTINGS, "Settings"),
            (0, None),
            (CMD_TEST_LOGIN, "Test Login Reminder"),
            (CMD_TEST_LOGOUT, "Test Logout Reminder"),
            (0, None),
            (CMD_VIEW_LOGS, "View Logs"),
            (0, None),
            (CMD_EXIT, "Exit"),
        ]
        for cmd, text in items:
            if cmd == 0:
                win32gui.AppendMenu(hmenu, win32con.MF_SEPARATOR, 0, "")
            else:
                win32gui.AppendMenu(hmenu, win32con.MF_STRING, cmd, text)

        pos = win32gui.GetCursorPos()
        logging.debug("Showing context menu (pos=%s)", pos)
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST,
                              0, 0, 0, 0,
                              win32con.SWP_NOSIZE | win32con.SWP_NOMOVE)
        win32gui.SetForegroundWindow(self.hwnd)
        selected = win32gui.TrackPopupMenu(
            hmenu,
            win32con.TPM_LEFTALIGN | win32con.TPM_RIGHTBUTTON | win32con.TPM_RETURNCMD,
            pos[0], pos[1], 0, self.hwnd, None,
        )
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
        win32gui.DestroyMenu(hmenu)
        if selected:
            logging.debug("Menu selected: cmd=%d", selected)
            self._dispatch_menu(selected)
        else:
            logging.debug("Menu dismissed (no selection)")

    def _dispatch_menu(self, cmd):
        if cmd == CMD_DASHBOARD:
            self.app.root.after(0, self.app.show_dashboard)
        elif cmd == CMD_SETTINGS:
            self.app.root.after(0, self.app.show_settings)
        elif cmd == CMD_TEST_LOGIN:
            self.app.test_reminder("login")
        elif cmd == CMD_TEST_LOGOUT:
            self.app.test_reminder("logout")
        elif cmd == CMD_VIEW_LOGS:
            self._open_logs()
        elif cmd == CMD_EXIT:
            self.app.root.after(0, self.app.shutdown)

    def _open_logs(self):
        try:
            os.startfile(str(self.app.app_dir / LOG_FILE))
        except Exception as e:
            logging.error("Failed to open log: %s", e)

    # ---- tooltip ----------------------------------------------------------

    def _build_tooltip(self):
        try:
            sch = self.app.schedule_manager.get_schedule(
                self.app.config.is_dst_active())
            st = self.app.state
            lines = [
                APP_NAME, "",
                f"Mode: {sch['mode_name']}",
                f"Shift Start: {sch['shift_start'].strftime(TIME_FORMAT)}",
                f"Shift End: {sch['shift_end'].strftime(TIME_FORMAT)}",
                "",
                "Login: " + ("Done" if st["login_acknowledged"]
                             else ("N/A" if not sch["login_required"] else "Pending")),
                "Logout: " + ("Done" if st["logout_acknowledged"]
                              else ("N/A" if not sch["logout_required"] else "Pending")),
            ]
            nxt = self.app._get_next_reminder_time()
            if nxt:
                lines.append(f"Next: {nxt.strftime(TIME_FORMAT)}")
            return "\n".join(lines)
        except Exception:
            return APP_NAME
