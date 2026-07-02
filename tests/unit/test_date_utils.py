"""Tests for date parsing and sorting utilities."""

from datetime import datetime, timedelta

import pytest

from doral_courts.utils.date_utils import (
    date_sort_key,
    from_iso_date,
    parse_date_input,
    time_sort_key,
    to_iso_date,
)


class TestParseDateInput:
    def test_none_defaults_to_today(self):
        assert parse_date_input(None) == datetime.now().strftime("%m/%d/%Y")

    @pytest.mark.parametrize("value", ["today", "now", "TODAY", "Now"])
    def test_today_keywords(self, value):
        assert parse_date_input(value) == datetime.now().strftime("%m/%d/%Y")

    def test_tomorrow(self):
        expected = (datetime.now() + timedelta(days=1)).strftime("%m/%d/%Y")
        assert parse_date_input("tomorrow") == expected

    def test_yesterday(self):
        expected = (datetime.now() - timedelta(days=1)).strftime("%m/%d/%Y")
        assert parse_date_input("yesterday") == expected

    @pytest.mark.parametrize("offset", [3, 7, 30])
    def test_positive_offset(self, offset):
        expected = (datetime.now() + timedelta(days=offset)).strftime("%m/%d/%Y")
        assert parse_date_input(f"+{offset}") == expected

    def test_negative_offset(self):
        expected = (datetime.now() - timedelta(days=2)).strftime("%m/%d/%Y")
        assert parse_date_input("-2") == expected

    def test_absolute_mm_dd_yyyy(self):
        assert parse_date_input("07/12/2025") == "07/12/2025"

    def test_iso_format_is_converted(self):
        assert parse_date_input("2025-07-12") == "07/12/2025"

    def test_invalid_mm_dd_yyyy_raises(self):
        # 13 is not a valid month
        with pytest.raises(ValueError):
            parse_date_input("13/45/2025")

    def test_unparseable_raises_value_error(self):
        with pytest.raises(ValueError):
            parse_date_input("not-a-date")

    def test_huge_offset_raises_value_error_not_overflow(self):
        # Must surface as ValueError, not an uncaught OverflowError.
        with pytest.raises(ValueError):
            parse_date_input("+999999999999")

    def test_mm_dd_takes_precedence_over_european(self):
        # 12/07/2025 matches MM/DD/YYYY first => December 7th, not July 12th.
        assert parse_date_input("12/07/2025") == "12/07/2025"


class TestDateSortKey:
    def test_orders_chronologically_not_lexically(self):
        dates = ["02/01/2025", "01/01/2027", "12/31/2024"]
        ordered = sorted(dates, key=date_sort_key)
        assert ordered == ["12/31/2024", "02/01/2025", "01/01/2027"]

    def test_unparseable_sorts_last(self):
        keyed = sorted(["bogus", "01/01/2025"], key=date_sort_key)
        assert keyed[0] == "01/01/2025"
        assert keyed[-1] == "bogus"


class TestIsoConversion:
    def test_to_iso_from_mmddyyyy(self):
        assert to_iso_date("07/12/2025") == "2025-07-12"

    def test_to_iso_idempotent(self):
        assert to_iso_date("2025-07-12") == "2025-07-12"

    def test_from_iso_to_mmddyyyy(self):
        assert from_iso_date("2025-07-12") == "07/12/2025"

    def test_from_iso_idempotent(self):
        assert from_iso_date("07/12/2025") == "07/12/2025"

    def test_round_trip(self):
        assert from_iso_date(to_iso_date("12/31/2025")) == "12/31/2025"

    def test_unparseable_passthrough(self):
        assert to_iso_date("garbage") == "garbage"
        assert from_iso_date("garbage") == "garbage"

    def test_empty_passthrough(self):
        assert to_iso_date("") == ""
        assert from_iso_date("") == ""


class TestTimeSortKey:
    def test_orders_numerically_not_lexically(self):
        times = ["10:00 am", "8:00 am", "9:00 am", "1:00 pm"]
        ordered = sorted(times, key=time_sort_key)
        assert ordered == ["8:00 am", "9:00 am", "10:00 am", "1:00 pm"]

    def test_am_pm_handling(self):
        assert time_sort_key("12:00 am") < time_sort_key("12:00 pm")
        assert time_sort_key("11:59 am") < time_sort_key("12:00 pm")

    def test_unparseable_sorts_last(self):
        ordered = sorted(["???", "8:00 am"], key=time_sort_key)
        assert ordered[0] == "8:00 am"
