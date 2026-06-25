"""
Utility functions and constants for Attendance Reminder.

Provides:
  - Application constants and default settings
  - US DST detection
  - Windows API helpers (workstation lock check, taskbar flashing, auto-start)
  - Tray icon image generation
  - Logging setup
  - Sound playback
"""

import os
import sys
import logging
import ctypes
import winsound
import winreg
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

APP_NAME = "Attendance Reminder"
APP_DIR_NAME = "AttendanceReminder"
SETTINGS_FILE = "settings.json"
LOG_FILE = "attendance_reminder.log"
BACKUP_FILE = "settings.backup.json"
MUTEX_NAME = "AttendanceReminder_8F4E2B1A-9C3D-4E5F-8A7B-6C5D4E3F2A1B"

ICON_SIZE = (64, 64)
ICON_GREEN = (0, 180, 0)
ICON_YELLOW = (255, 200, 0)
ICON_RED = (220, 0, 0)

CHECK_INTERVAL_MS = 30000
SNOOZE_DEFAULT_MIN = 5
CRITICAL_RESHOW_SEC = 60
UNLOCK_POLL_INTERVAL = 2

TIME_FORMAT = "%I:%M:%S %p"
DATETIME_FORMAT = "%Y-%m-%d %I:%M:%S %p"

AUTOSTART_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_REG_KEY = "AttendanceReminder"

DEFAULT_SETTINGS = {
    "login_hour": 22,
    "login_minute": 59,
    "logout_hour": 8,
    "logout_minute": 0,
    "login_critical_hour": 23,
    "login_critical_minute": 49,
    "login_unlock_start_hour": 22,
    "login_unlock_start_minute": 59,
    "login_unlock_end_hour": 0,
    "login_unlock_end_minute": 59,
    "logout_unlock_start_hour": 8,
    "logout_unlock_start_minute": 0,
    "logout_unlock_end_hour": 10,
    "logout_unlock_end_minute": 0,
    "dst_login_hour": 22,
    "dst_login_minute": 0,
    "dst_logout_hour": 7,
    "dst_logout_minute": 0,
    "dst_login_critical_hour": 22,
    "dst_login_critical_minute": 50,
    "dst_login_unlock_start_hour": 22,
    "dst_login_unlock_start_minute": 0,
    "dst_login_unlock_end_hour": 23,
    "dst_login_unlock_end_minute": 59,
    "dst_logout_unlock_start_hour": 7,
    "dst_logout_unlock_start_minute": 0,
    "dst_logout_unlock_end_hour": 9,
    "dst_logout_unlock_end_minute": 0,
    "snooze_minutes": 5,
    "reminders_enabled": True,
    "auto_start": True,
    "sound_enabled": True,
    "dst_auto_detect": True,
    "dst_override": None,
}

# --------------------------------------------------------------------------
# Path Helpers
# --------------------------------------------------------------------------

def get_app_data_dir():
    """Get or create the application data directory under %APPDATA%."""
    app_data = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    app_dir = app_data / APP_DIR_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

# --------------------------------------------------------------------------
# US DST Detection
# --------------------------------------------------------------------------

def is_us_dst(dt=None):
    """
    Determine if US Daylight Saving Time is currently active.

    US DST runs from the second Sunday of March (2:00 AM) to the
    first Sunday of November (2:00 AM).
    """
    if dt is None:
        dt = datetime.now()
    year = dt.year

    march_1 = datetime(year, 3, 1)
    days_to_first_sunday = (6 - march_1.weekday()) % 7
    dst_start = march_1 + timedelta(days=days_to_first_sunday + 7)
    dst_start = dst_start.replace(hour=2, minute=0, second=0, microsecond=0)

    nov_1 = datetime(year, 11, 1)
    days_to_first_sunday = (6 - nov_1.weekday()) % 7
    dst_end = nov_1 + timedelta(days=days_to_first_sunday)
    dst_end = dst_end.replace(hour=2, minute=0, second=0, microsecond=0)

    return dst_start <= dt < dst_end

# --------------------------------------------------------------------------
# Windows API Helpers
# --------------------------------------------------------------------------

def is_workstation_locked():
    """Check if the Windows workstation is currently locked via OpenDesktop."""
    try:
        user32 = ctypes.windll.user32
        DESKTOP_SWITCHDESKTOP = 0x0100
        hdesk = user32.OpenDesktopW("default", 0, False, DESKTOP_SWITCHDESKTOP)
        if hdesk:
            user32.CloseDesktop(hdesk)
            return False
        return True
    except Exception:
        return False


class FLASHWINFO(ctypes.Structure):
    """Windows FLASHWINFO structure for FlashWindowEx."""
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("hwnd", ctypes.c_void_p),
        ("dwFlags", ctypes.c_uint),
        ("uCount", ctypes.c_uint),
        ("dwTimeout", ctypes.c_uint),
    ]


def flash_taskbar_window(hwnd, count=5):
    """Flash the taskbar button for a given window handle."""
    try:
        FLASHW_ALL = 0x03
        FLASHW_TIMERNOFG = 0x0C
        info = FLASHWINFO(
            ctypes.sizeof(FLASHWINFO),
            hwnd,
            FLASHW_ALL | FLASHW_TIMERNOFG,
            count,
            0,
        )
        ctypes.windll.user32.FlashWindowEx(ctypes.byref(info))
    except Exception:
        pass


def get_window_hwnd(widget):
    """Get the top-level window HWND for a Tkinter widget (GA_ROOT = 2)."""
    try:
        return ctypes.windll.user32.GetAncestor(widget.winfo_id(), 2)
    except Exception:
        return None

# --------------------------------------------------------------------------
# Sound
# --------------------------------------------------------------------------

def play_notification_sound(urgent=False):
    """Play a Windows notification sound via winsound."""
    try:
        if urgent:
            winsound.MessageBeep(winsound.MB_ICONHAND)
        else:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass

# --------------------------------------------------------------------------
# Auto-start with Windows (Registry)
# --------------------------------------------------------------------------

def set_auto_start(enabled, exe_path=None):
    """Enable or disable automatic startup via HKCU registry Run key."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            AUTOSTART_REG_PATH,
            0,
            winreg.KEY_SET_VALUE,
        )
        if enabled:
            if exe_path:
                val = exe_path
            elif getattr(sys, "frozen", False):
                val = f'"{sys.executable}"'
            else:
                val = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
            winreg.SetValueEx(key, AUTOSTART_REG_KEY, 0, winreg.REG_SZ, val)
            logging.info("Auto-start enabled: %s", val)
        else:
            try:
                winreg.DeleteValue(key, AUTOSTART_REG_KEY)
                logging.info("Auto-start disabled")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        logging.error("Failed to set auto-start: %s", e)
        return False


def is_auto_start_enabled():
    """Check if auto-start with Windows is currently enabled."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            AUTOSTART_REG_PATH,
            0,
            winreg.KEY_READ,
        )
        try:
            winreg.QueryValueEx(key, AUTOSTART_REG_KEY)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False

# --------------------------------------------------------------------------
# Tray Icon Image Generation
# --------------------------------------------------------------------------

def create_tray_icon_image(color):
    """Create a colored circle PIL image for the system tray icon."""
    img = Image.new("RGBA", ICON_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 4
    draw.ellipse(
        [margin, margin, ICON_SIZE[0] - margin, ICON_SIZE[1] - margin],
        fill=color + (255,),
    )
    return img

# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------

def setup_logging(log_path):
    """
    Configure the Python logging system.

    Removes any existing handlers, then adds a file handler (DEBUG+) and a
    console handler (INFO+).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        root_logger.addHandler(fh)
    except Exception:
        pass

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    root_logger.addHandler(ch)

# --------------------------------------------------------------------------
# Single Instance
# --------------------------------------------------------------------------

def is_already_running():
    """Check if another instance is running using a named mutex."""
    try:
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
        if kernel32.GetLastError() == 183:
            kernel32.CloseHandle(mutex)
            return True
        return False
    except Exception:
        return False
