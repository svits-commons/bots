import holidays
import pytz

from datetime import timedelta, datetime


def get_work_days(start_date: datetime, end_date: datetime) -> int:
    us_holidays = holidays.US()
    day_count = 0
    current = start_date
    while current <= end_date:
        is_weekday = current.weekday() < 5
        is_holiday = current in us_holidays
        if is_weekday and not is_holiday:
            day_count += 1
        current += timedelta(days=1)
    return day_count


def utcnow():
    now = datetime.now(pytz.UTC)
    now = now.replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return now.timestamp()
