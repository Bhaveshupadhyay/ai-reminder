import re
from datetime import datetime, time, timedelta, timezone
from typing import Optional
import pytz
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU
from app.core.logging import logger

WEEKDAYS = {
    "monday": MO,
    "tuesday": TU,
    "wednesday": WE,
    "thursday": TH,
    "friday": FR,
    "saturday": SA,
    "sunday": SU,
}


class DateService:
    """Service for resolving and normalizing natural language relative deadlines into UTC datetimes."""

    @staticmethod
    def get_user_timezone(tz_name: Optional[str]) -> pytz.BaseTzInfo:
        if not tz_name:
            return pytz.UTC
        try:
            return pytz.timezone(tz_name)
        except Exception:
            logger.warning(f"Invalid timezone '{tz_name}', falling back to UTC")
            return pytz.UTC

    @classmethod
    def parse_relative_deadline(
        cls,
        deadline_text: Optional[str],
        reference_time: Optional[datetime] = None,
        user_timezone_str: str = "UTC",
    ) -> Optional[datetime]:
        """
        Parse relative natural language date expression into an absolute UTC datetime.
        """
        if not deadline_text or not deadline_text.strip():
            return None

        text = deadline_text.strip().lower()
        user_tz = cls.get_user_timezone(user_timezone_str)

        # Base reference time in user local timezone
        if reference_time is None:
            now_utc = datetime.now(timezone.utc)
        else:
            if reference_time.tzinfo is None:
                now_utc = reference_time.replace(tzinfo=timezone.utc)
            else:
                now_utc = reference_time.astimezone(timezone.utc)

        now_local = now_utc.astimezone(user_tz)

        # 1. 'tomorrow'
        if "tomorrow" in text:
            target_date = now_local.date() + timedelta(days=1)
            time_match = re.search(r"(?:at|by)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text)
            if time_match:
                hr = int(time_match.group(1))
                mn = int(time_match.group(2) or 0)
                meridiem = time_match.group(3)
                if meridiem == "pm" and hr < 12:
                    hr += 12
                elif meridiem == "am" and hr == 12:
                    hr = 0
                target_time = time(hr, mn)
            else:
                target_time = time(17, 0)  # Default 5:00 PM local
            local_dt = user_tz.localize(datetime.combine(target_date, target_time))
            return local_dt.astimezone(timezone.utc)

        # 2. 'today' / 'tonight' / 'this evening'
        if "today" in text or "tonight" in text or "this evening" in text:
            target_date = now_local.date()
            if "tonight" in text or "this evening" in text:
                target_time = time(20, 0)
            else:
                target_time = time(18, 0)
            local_dt = user_tz.localize(datetime.combine(target_date, target_time))
            if local_dt <= now_local:
                local_dt = now_local + timedelta(hours=2)
            return local_dt.astimezone(timezone.utc)

        # 3. 'after 6' or 'after 6pm' or 'after 6:00'
        after_match = re.search(r"after\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text)
        if after_match:
            hr = int(after_match.group(1))
            mn = int(after_match.group(2) or 0)
            meridiem = after_match.group(3)
            if meridiem == "pm" and hr < 12:
                hr += 12
            elif meridiem is None and hr <= 11:
                hr += 12

            target_date = now_local.date()
            target_time = time(hr, mn)
            local_dt = user_tz.localize(datetime.combine(target_date, target_time))
            if local_dt <= now_local:
                local_dt = local_dt + timedelta(days=1)
            return local_dt.astimezone(timezone.utc)

        # 4. 'in X hours' / 'in X minutes' / 'in X days'
        rel_match = re.search(r"in\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(hour|minute|day|week)s?", text)
        if rel_match:
            num_words = {
                "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            }
            raw_qty = rel_match.group(1)
            qty = num_words.get(raw_qty, None) or int(raw_qty)
            unit = rel_match.group(2)
            if unit == "minute":
                res_local = now_local + timedelta(minutes=qty)
            elif unit == "hour":
                res_local = now_local + timedelta(hours=qty)
            elif unit == "day":
                res_local = now_local + timedelta(days=qty)
            elif unit == "week":
                res_local = now_local + timedelta(weeks=qty)
            return res_local.astimezone(timezone.utc)

        # 5. 'next week' / 'sometime next week'
        if "next week" in text:
            days_ahead = (7 - now_local.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            target_date = now_local.date() + timedelta(days=days_ahead)
            local_dt = user_tz.localize(datetime.combine(target_date, time(10, 0)))
            return local_dt.astimezone(timezone.utc)

        # 6. Specific Day of week: 'friday', 'next monday', etc.
        for day_name, day_code in WEEKDAYS.items():
            if day_name in text:
                target_dt = now_local + relativedelta(weekday=day_code(+1))
                target_dt = target_dt.replace(hour=17, minute=0, second=0, microsecond=0)
                return target_dt.astimezone(timezone.utc)

        # 7. Fallback generic dateutil parser
        try:
            parsed = date_parser.parse(text, fuzzy=True, default=now_local)
            if parsed.tzinfo is None:
                parsed = user_tz.localize(parsed)
            return parsed.astimezone(timezone.utc)
        except Exception:
            logger.debug(f"Could not parse relative date '{text}'")
            return None
