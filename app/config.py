"""
Configuration management for Attendance Reminder.

Loads, saves, imports, and exports settings from a JSON file. Falls back to
defaults on corruption and maintains automatic backups.
"""

import json
import shutil
import logging
from pathlib import Path

from .utils import DEFAULT_SETTINGS, SETTINGS_FILE, BACKUP_FILE, is_us_dst


class ConfigManager:
    """Manages application settings persisted to settings.json."""

    def __init__(self, app_dir):
        self.app_dir = app_dir
        self.settings_path = app_dir / SETTINGS_FILE
        self.backup_path = app_dir / BACKUP_FILE
        self.settings = self._load()

    def _load(self):
        """Load settings from file, trying the backup if the main file is corrupt."""
        for path in (self.settings_path, self.backup_path):
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    merged = dict(DEFAULT_SETTINGS)
                    merged.update(data)
                    logging.info("Settings loaded from %s", path)
                    return merged
                except (json.JSONDecodeError, OSError) as e:
                    logging.warning("Failed to load settings from %s: %s", path, e)
        logging.info("Using default settings")
        return dict(DEFAULT_SETTINGS)

    def save(self):
        """Save current settings to file, creating a backup of the previous state."""
        if self.settings_path.exists():
            try:
                shutil.copy2(self.settings_path, self.backup_path)
            except OSError:
                pass
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2, ensure_ascii=False)
        logging.info("Settings saved")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value

    def import_settings(self, filepath):
        """Import settings from an external JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            imported = json.load(f)
        merged = dict(DEFAULT_SETTINGS)
        merged.update(imported)
        self.settings = merged
        self.save()
        logging.info("Settings imported from %s", filepath)

    def export_settings(self, filepath):
        """Export current settings to an external JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2, ensure_ascii=False)
        logging.info("Settings exported to %s", filepath)

    def is_dst_active(self):
        """Determine whether the DST schedule should be used."""
        if not self.get("dst_auto_detect", True):
            override = self.get("dst_override")
            if override is not None:
                return bool(override)
        return is_us_dst()
