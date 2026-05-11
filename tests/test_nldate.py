from datetime import date

import pytest

from nldate import parse


def test_absolute_month_name_with_ordinal() -> None:
    assert parse("December 1st, 2025") == date(2025, 12, 1)


def test_absolute_iso_date() -> None:
    assert parse("2025-12-01") == date(2025, 12, 1)


def test_absolute_year_slash_date() -> None:
    assert parse("2025/12/04") == date(2025, 12, 4)


def test_absolute_slash_date_uses_reference_year() -> None:
    assert parse("12/1", today=date(2025, 6, 15)) == date(2025, 12, 1)


def test_absolute_month_name_with_two_digit_year() -> None:
    assert parse("Dec 1, 25") == date(2025, 12, 1)


def test_days_before_absolute_date() -> None:
    assert parse("5 days before December 1st, 2025") == date(2025, 11, 26)


def test_weeks_after_absolute_date() -> None:
    assert parse("2 weeks after Jan 3, 2025") == date(2025, 1, 17)


def test_next_tuesday_is_strictly_future() -> None:
    assert parse("next Tuesday", today=date(2025, 11, 25)) == date(2025, 12, 2)


def test_next_tuesday_from_monday() -> None:
    assert parse("next Tuesday", today=date(2025, 11, 24)) == date(2025, 11, 25)


def test_next_weekday_abbreviation_with_period() -> None:
    assert parse("next Tue.", today=date(2025, 11, 24)) == date(2025, 11, 25)


def test_last_friday() -> None:
    assert parse("last Friday", today=date(2025, 11, 24)) == date(2025, 11, 21)


def test_this_friday_can_be_later_in_same_week() -> None:
    assert parse("this Friday", today=date(2025, 11, 24)) == date(2025, 11, 28)


def test_in_three_days() -> None:
    assert parse("in 3 days", today=date(2025, 11, 24)) == date(2025, 11, 27)


def test_in_three_days_as_word() -> None:
    assert parse("in three days", today=date(2025, 11, 24)) == date(2025, 11, 27)


def test_two_weeks_ago() -> None:
    assert parse("2 weeks ago", today=date(2025, 11, 24)) == date(2025, 11, 10)


def test_a_week_ago() -> None:
    assert parse("a week ago", today=date(2025, 11, 24)) == date(2025, 11, 17)


def test_month_arithmetic_clamps_to_valid_day() -> None:
    assert parse("1 month after January 31st, 2025") == date(2025, 2, 28)


def test_compound_offset_before_absolute_date() -> None:
    assert parse("2 years, 3 months before Dec. 1, 2025") == date(2023, 9, 1)


def test_leading_on_the_absolute_date() -> None:
    assert parse("on the December 1st, 2025") == date(2025, 12, 1)


def test_tomorrow() -> None:
    assert parse("tomorrow", today=date(2025, 11, 24)) == date(2025, 11, 25)


def test_day_after_tomorrow() -> None:
    assert parse("the day after tomorrow", today=date(2025, 11, 24)) == date(2025, 11, 26)


def test_invalid_expression_raises_value_error() -> None:
    with pytest.raises(ValueError):
        parse("not a date")
