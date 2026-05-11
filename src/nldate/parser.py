"""Parse a focused set of natural-language date expressions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum


class _Direction(Enum):
    BEFORE = -1
    AFTER = 1


@dataclass(frozen=True)
class _RelativeAmount:
    value: int
    unit: str


_MONTHS: dict[str, int] = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sept": 9,
    "sep": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

_WEEKDAYS: dict[str, int] = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "tues": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}

_UNIT_ALIASES: dict[str, str] = {
    "day": "day",
    "days": "day",
    "week": "week",
    "weeks": "week",
    "month": "month",
    "months": "month",
    "year": "year",
    "years": "year",
}
_SMALL_NUMBERS: dict[str, int] = {
    "zero": 0,
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}
_TENS: dict[str, int] = {
    "twenty": 20,
    "thirty": 30,
}
_NUMBER_WORDS: dict[str, int] = (
    _SMALL_NUMBERS
    | _TENS
    | {
        f"{tens_name} {small_name}": tens_value + small_value
        for tens_name, tens_value in _TENS.items()
        for small_name, small_value in _SMALL_NUMBERS.items()
        if 1 <= small_value <= 9
    }
)
_AMOUNT_PATTERN = r"\d+|[a-z]+(?:[-\s][a-z]+)?"

_ORDINAL_SUFFIX_RE = re.compile(r"(?<=\d)(st|nd|rd|th)\b", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")
_ISO_DATE_RE = re.compile(r"^(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})$")
_YEAR_SLASH_DATE_RE = re.compile(r"^(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})$")
_SLASH_DATE_RE = re.compile(r"^(?P<month>\d{1,2})/(?P<day>\d{1,2})(?:/(?P<year>\d{2,4}))?$")
_MONTH_DATE_RE = re.compile(r"^(?P<month>[a-z]+)\.?\s+(?P<day>\d{1,2})(?:,?\s+(?P<year>\d{2,4}))?$")
_DATE_MONTH_RE = re.compile(r"^(?P<day>\d{1,2})\s+(?P<month>[a-z]+)\.?(?:,?\s+(?P<year>\d{2,4}))?$")
_RELATIVE_PREFIX_RE = re.compile(
    rf"^(?P<amount>{_AMOUNT_PATTERN})\s+(?P<unit>days?|weeks?|months?|years?)\s+"
    rf"(?P<direction>before|after)\s+(?P<target>.+)$"
)
_RELATIVE_IN_RE = re.compile(
    rf"^in\s+(?P<amount>{_AMOUNT_PATTERN})\s+(?P<unit>days?|weeks?|months?|years?)$"
)
_RELATIVE_AGO_RE = re.compile(
    rf"^(?P<amount>{_AMOUNT_PATTERN})\s+(?P<unit>days?|weeks?|months?|years?)\s+ago$"
)
_RELATIVE_FROM_NOW_RE = re.compile(
    rf"^(?P<amount>{_AMOUNT_PATTERN})\s+(?P<unit>days?|weeks?|months?|years?)\s+"
    rf"from\s+(?:now|today)$"
)
_NEXT_LAST_WEEKDAY_RE = re.compile(r"^(?P<direction>next|last)\s+(?P<weekday>[a-z]+)\.?$")
_THIS_WEEKDAY_RE = re.compile(r"^this\s+(?P<weekday>[a-z]+)\.?$")


def parse(s: str, today: date | None = None) -> date:
    """Return the concrete date represented by *s*.

    Supported expressions include absolute dates such as ``December 1st, 2025``,
    offsets such as ``5 days before December 1st, 2025``, and relative dates
    such as ``next Tuesday``. When omitted, *today* defaults to the system date.
    """

    reference = today or date.today()
    normalized = _normalize(s)
    if not normalized:
        msg = "Cannot parse an empty date expression"
        raise ValueError(msg)

    return _parse_normalized(normalized, reference)


def _parse_normalized(s: str, today: date) -> date:
    match s:
        case "today":
            return today
        case "tomorrow":
            return today + timedelta(days=1)
        case "day after tomorrow":
            return today + timedelta(days=2)
        case "yesterday":
            return today - timedelta(days=1)
        case "day before yesterday":
            return today - timedelta(days=2)
        case "next week":
            return today + timedelta(weeks=1)
        case "last week":
            return today - timedelta(weeks=1)
        case "next month":
            return _add_months(today, 1)
        case "last month":
            return _add_months(today, -1)
        case "next year":
            return _add_years(today, 1)
        case "last year":
            return _add_years(today, -1)

    if match := _RELATIVE_PREFIX_RE.match(s):
        amount = _relative_amount(match)
        direction = _Direction[match.group("direction").upper()]
        target = _parse_normalized(match.group("target"), today)
        return _apply_relative(target, amount, direction)

    if match := _RELATIVE_IN_RE.match(s):
        return _apply_relative(today, _relative_amount(match), _Direction.AFTER)

    if match := _RELATIVE_AGO_RE.match(s):
        return _apply_relative(today, _relative_amount(match), _Direction.BEFORE)

    if match := _RELATIVE_FROM_NOW_RE.match(s):
        return _apply_relative(today, _relative_amount(match), _Direction.AFTER)

    if match := _NEXT_LAST_WEEKDAY_RE.match(s):
        weekday = _parse_weekday(match.group("weekday"))
        if match.group("direction") == "next":
            return _next_weekday(today, weekday)
        return _last_weekday(today, weekday)

    if match := _THIS_WEEKDAY_RE.match(s):
        return _this_weekday(today, _parse_weekday(match.group("weekday")))

    weekday_key = s.rstrip(".")
    if weekday_key in _WEEKDAYS:
        return _this_weekday(today, _WEEKDAYS[weekday_key])

    if parsed := _parse_absolute_date(s, today):
        return parsed

    msg = f"Could not parse date expression: {s!r}"
    raise ValueError(msg)


def _normalize(s: str) -> str:
    lowered = s.strip().lower().replace(",", " ")
    without_ordinals = _ORDINAL_SUFFIX_RE.sub("", lowered)
    normalized = _WHITESPACE_RE.sub(" ", without_ordinals).strip()
    for prefix in ("on the ", "on ", "the "):
        if normalized.startswith(prefix):
            return normalized.removeprefix(prefix)
    return normalized


def _relative_amount(match: re.Match[str]) -> _RelativeAmount:
    unit = _UNIT_ALIASES[match.group("unit")]
    return _RelativeAmount(value=_parse_amount(match.group("amount")), unit=unit)


def _parse_amount(amount: str) -> int:
    if amount.isdigit():
        return int(amount)

    normalized = amount.replace("-", " ")
    try:
        return _NUMBER_WORDS[normalized]
    except KeyError as exc:
        msg = f"Unknown relative amount: {amount!r}"
        raise ValueError(msg) from exc


def _apply_relative(base: date, amount: _RelativeAmount, direction: _Direction) -> date:
    sign = direction.value
    if amount.unit == "day":
        return base + timedelta(days=sign * amount.value)
    if amount.unit == "week":
        return base + timedelta(weeks=sign * amount.value)
    if amount.unit == "month":
        return _add_months(base, sign * amount.value)
    if amount.unit == "year":
        return _add_years(base, sign * amount.value)

    msg = f"Unsupported relative unit: {amount.unit!r}"
    raise ValueError(msg)


def _parse_weekday(weekday: str) -> int:
    key = weekday.rstrip(".")
    try:
        return _WEEKDAYS[key]
    except KeyError as exc:
        msg = f"Unknown weekday: {weekday!r}"
        raise ValueError(msg) from exc


def _next_weekday(base: date, weekday: int) -> date:
    days_ahead = (weekday - base.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return base + timedelta(days=days_ahead)


def _last_weekday(base: date, weekday: int) -> date:
    days_behind = (base.weekday() - weekday) % 7
    if days_behind == 0:
        days_behind = 7
    return base - timedelta(days=days_behind)


def _this_weekday(base: date, weekday: int) -> date:
    return base + timedelta(days=weekday - base.weekday())


def _parse_absolute_date(s: str, today: date) -> date | None:
    if match := _ISO_DATE_RE.match(s):
        return date(
            year=int(match.group("year")),
            month=int(match.group("month")),
            day=int(match.group("day")),
        )

    if match := _YEAR_SLASH_DATE_RE.match(s):
        return date(
            year=int(match.group("year")),
            month=int(match.group("month")),
            day=int(match.group("day")),
        )

    if match := _SLASH_DATE_RE.match(s):
        return date(
            year=_coerce_year(match.group("year"), today),
            month=int(match.group("month")),
            day=int(match.group("day")),
        )

    if match := _MONTH_DATE_RE.match(s):
        return date(
            year=_coerce_year(match.group("year"), today),
            month=_parse_month(match.group("month")),
            day=int(match.group("day")),
        )

    if match := _DATE_MONTH_RE.match(s):
        return date(
            year=_coerce_year(match.group("year"), today),
            month=_parse_month(match.group("month")),
            day=int(match.group("day")),
        )

    return None


def _parse_month(month: str) -> int:
    try:
        return _MONTHS[month.rstrip(".")]
    except KeyError as exc:
        msg = f"Unknown month: {month!r}"
        raise ValueError(msg) from exc


def _coerce_year(year: str | None, today: date) -> int:
    if year is None:
        return today.year

    if len(year) == 2:
        number = int(year)
        return 2000 + number if number <= 68 else 1900 + number

    return int(year)


def _add_months(base: date, months: int) -> date:
    month_index = base.month - 1 + months
    year = base.year + month_index // 12
    month = month_index % 12 + 1
    day = min(base.day, _days_in_month(year, month))
    return date(year, month, day)


def _add_years(base: date, years: int) -> date:
    year = base.year + years
    day = min(base.day, _days_in_month(year, base.month))
    return date(year, base.month, day)


def _days_in_month(year: int, month: int) -> int:
    next_month = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return (next_month - timedelta(days=1)).day
