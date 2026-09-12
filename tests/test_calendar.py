"""Federal Reserve calendar tests."""

from datetime import date

from achlens.core.calendar import (
    is_federal_reserve_holiday,
    next_federal_reserve_business_day,
)


def test_official_k8_holiday_dates() -> None:
    assert is_federal_reserve_holiday(date(2026, 1, 1))
    assert is_federal_reserve_holiday(date(2026, 7, 4))
    assert is_federal_reserve_holiday(date(2030, 12, 25))
    assert not is_federal_reserve_holiday(date(2026, 9, 12))


def test_next_business_day_skips_weekends_and_holidays() -> None:
    assert next_federal_reserve_business_day(date(2026, 7, 3)) == date(2026, 7, 6)
    assert next_federal_reserve_business_day(date(2026, 9, 4)) == date(2026, 9, 8)
