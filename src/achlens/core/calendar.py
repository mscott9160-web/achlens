"""Federal Reserve holiday dates from the official K.8 schedule."""

from datetime import date, timedelta

SOURCE_URL = "https://www.federalreserve.gov/aboutthefed/k8.htm"
RETRIEVED = "2026-09-12"

# K.8 holiday dates for 2026-2030. These are Federal Reserve schedule dates,
# not a bank-specific settlement calendar.
FEDERAL_RESERVE_HOLIDAYS: frozenset[date] = frozenset(
    {
        date(2026, 1, 1),
        date(2026, 1, 19),
        date(2026, 2, 16),
        date(2026, 5, 25),
        date(2026, 6, 19),
        date(2026, 7, 4),
        date(2026, 9, 7),
        date(2026, 10, 12),
        date(2026, 11, 11),
        date(2026, 11, 26),
        date(2026, 12, 25),
        date(2027, 1, 1),
        date(2027, 1, 18),
        date(2027, 2, 15),
        date(2027, 5, 31),
        date(2027, 6, 19),
        date(2027, 7, 4),
        date(2027, 9, 6),
        date(2027, 10, 11),
        date(2027, 11, 11),
        date(2027, 11, 25),
        date(2027, 12, 25),
        date(2028, 1, 1),
        date(2028, 1, 17),
        date(2028, 2, 21),
        date(2028, 5, 29),
        date(2028, 6, 19),
        date(2028, 7, 4),
        date(2028, 9, 4),
        date(2028, 10, 9),
        date(2028, 11, 10),
        date(2028, 11, 23),
        date(2028, 12, 25),
        date(2029, 1, 1),
        date(2029, 1, 15),
        date(2029, 2, 19),
        date(2029, 5, 28),
        date(2029, 6, 19),
        date(2029, 7, 4),
        date(2029, 9, 3),
        date(2029, 10, 8),
        date(2029, 11, 12),
        date(2029, 11, 22),
        date(2029, 12, 25),
        date(2030, 1, 1),
        date(2030, 1, 21),
        date(2030, 2, 18),
        date(2030, 5, 27),
        date(2030, 6, 19),
        date(2030, 7, 4),
        date(2030, 9, 2),
        date(2030, 10, 14),
        date(2030, 11, 11),
        date(2030, 11, 28),
        date(2030, 12, 25),
    }
)


def is_federal_reserve_holiday(value: date) -> bool:
    """Return whether *value* is listed in the current K.8 schedule."""
    return value in FEDERAL_RESERVE_HOLIDAYS


def next_federal_reserve_business_day(value: date) -> date:
    """Return the next weekday not listed in the K.8 holiday schedule."""
    candidate = value + timedelta(days=1)
    while candidate.weekday() >= 5 or is_federal_reserve_holiday(candidate):
        candidate += timedelta(days=1)
    return candidate


__all__ = [
    "FEDERAL_RESERVE_HOLIDAYS",
    "RETRIEVED",
    "SOURCE_URL",
    "is_federal_reserve_holiday",
    "next_federal_reserve_business_day",
]
