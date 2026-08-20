from datetime import datetime, timezone
import pytest
from app.services.date_service import DateService


def test_parse_tomorrow():
    ref = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)
    res = DateService.parse_relative_deadline("tomorrow", reference_time=ref, user_timezone_str="UTC")
    assert res is not None
    assert res.year == 2026
    assert res.month == 8
    assert res.day == 20
    assert res.hour == 17  # Default 5:00 PM


def test_parse_next_week():
    ref = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)  # Wednesday
    res = DateService.parse_relative_deadline("next week", reference_time=ref, user_timezone_str="UTC")
    assert res is not None
    assert res > ref


def test_parse_relative_hours():
    ref = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)
    res = DateService.parse_relative_deadline("in 2 hours", reference_time=ref, user_timezone_str="UTC")
    assert res is not None
    assert (res - ref).total_seconds() == 7200


def test_parse_none():
    assert DateService.parse_relative_deadline(None) is None
    assert DateService.parse_relative_deadline("") is None
