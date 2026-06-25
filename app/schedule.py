"""
Schedule management for Attendance Reminder.

Calculates daily reminder schedules based on DST status and user
configuration. Determines which reminders are needed for each day of the week.
"""

from datetime import datetime, time as Time, timedelta


def _add_hours(t, hours):
    """Return a time object with the given hours added (wraps 24h)."""
    total = t.hour * 60 + t.minute + hours * 60
    total %= 24 * 60
    return Time(total // 60, total % 60)


def _add_minutes(t, minutes):
    """Return a time object with the given minutes added (wraps 24h)."""
    total = t.hour * 60 + t.minute + minutes
    total %= 24 * 60
    return Time(total // 60, total % 60)


class ScheduleManager:
    """Computes reminder schedules and provides time comparison helpers."""

    def __init__(self, config):
        self.config = config

    def get_schedule(self, dst_active):
        """
        Build a schedule dict for today based on DST status.

        Returns login/logout time windows, unlock detection windows, and
        whether each reminder type applies today.
        """
        today = datetime.now().weekday()
        login_required = today in (0, 1, 2, 3, 4)
        logout_required = today in (1, 2, 3, 4, 5)
        no_reminders = today == 6

        if dst_active:
            mode_name = "US DST"
            login_t = Time(self.config.get("dst_login_hour"), self.config.get("dst_login_minute"))
            logout_t = Time(self.config.get("dst_logout_hour"), self.config.get("dst_logout_minute"))
            login_crit = Time(
                self.config.get("dst_login_critical_hour"),
                self.config.get("dst_login_critical_minute"),
            )
            lu_start = Time(
                self.config.get("dst_login_unlock_start_hour"),
                self.config.get("dst_login_unlock_start_minute"),
            )
            lu_end = Time(
                self.config.get("dst_login_unlock_end_hour"),
                self.config.get("dst_login_unlock_end_minute"),
            )
            lou_start = Time(
                self.config.get("dst_logout_unlock_start_hour"),
                self.config.get("dst_logout_unlock_start_minute"),
            )
            lou_end = Time(
                self.config.get("dst_logout_unlock_end_hour"),
                self.config.get("dst_logout_unlock_end_minute"),
            )
        else:
            mode_name = "Regular"
            login_t = Time(self.config.get("login_hour"), self.config.get("login_minute"))
            logout_t = Time(self.config.get("logout_hour"), self.config.get("logout_minute"))
            login_crit = Time(
                self.config.get("login_critical_hour"),
                self.config.get("login_critical_minute"),
            )
            lu_start = Time(
                self.config.get("login_unlock_start_hour"),
                self.config.get("login_unlock_start_minute"),
            )
            lu_end = Time(
                self.config.get("login_unlock_end_hour"),
                self.config.get("login_unlock_end_minute"),
            )
            lou_start = Time(
                self.config.get("logout_unlock_start_hour"),
                self.config.get("logout_unlock_start_minute"),
            )
            lou_end = Time(
                self.config.get("logout_unlock_end_hour"),
                self.config.get("logout_unlock_end_minute"),
            )

        return {
            "login_required": login_required,
            "logout_required": logout_required,
            "no_reminders": no_reminders,
            "shift_start": _add_hours(login_t, 1),
            "shift_end": logout_t,
            "work_prep_time": _add_minutes(login_t, 55),
            "login_time": login_t,
            "logout_time": logout_t,
            "login_critical_time": login_crit,
            "login_unlock_start": lu_start,
            "login_unlock_end": lu_end,
            "logout_unlock_start": lou_start,
            "logout_unlock_end": lou_end,
            "mode_name": mode_name,
            "dst_active": dst_active,
        }

    @staticmethod
    def is_time_past(target_time):
        """Return True if the current time is >= target_time."""
        return datetime.now().time() >= target_time

    @staticmethod
    def is_time_in_range(start_time, end_time):
        """Return True if the current time falls within [start, end]."""
        return start_time <= datetime.now().time() <= end_time
