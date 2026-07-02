"""Date parsing and formatting utilities."""

import re
from datetime import datetime, timedelta
from typing import Optional


def parse_date_input(date_input: Optional[str] = None) -> str:
    """
    Parse date input supporting both absolute and relative formats.

    Args:
        date_input: Date string in various formats:
                   - None: defaults to today
                   - "today", "now": today
                   - "tomorrow": tomorrow
                   - "yesterday": yesterday
                   - "+N": N days from today (e.g., "+3")
                   - "-N": N days before today (e.g., "-2")
                   - "MM/DD/YYYY": absolute date

    Returns:
        Date string in MM/DD/YYYY format

    Raises:
        ValueError: If date format is invalid
    """
    if date_input is None or date_input.lower() in ["today", "now"]:
        target_date = datetime.now()
    elif date_input.lower() == "tomorrow":
        target_date = datetime.now() + timedelta(days=1)
    elif date_input.lower() == "yesterday":
        target_date = datetime.now() - timedelta(days=1)
    elif re.match(r"^[+-]\d+$", date_input):
        # Handle relative days like +3, -2
        days_offset = int(date_input)
        try:
            target_date = datetime.now() + timedelta(days=days_offset)
        except OverflowError as err:
            raise ValueError(f"Date offset out of range: {date_input}.") from err
    elif re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", date_input):
        # Handle MM/DD/YYYY format - validate it
        try:
            target_date = datetime.strptime(date_input, "%m/%d/%Y")
        except ValueError as err:
            raise ValueError(
                f"Invalid date format: {date_input}. Use MM/DD/YYYY format."
            ) from err
    else:
        # Try to parse other common formats
        common_formats = [
            "%Y-%m-%d",  # 2025-07-12
            "%m-%d-%Y",  # 07-12-2025
            "%d/%m/%Y",  # 12/07/2025 (European)
            "%Y/%m/%d",  # 2025/07/12
        ]

        target_date = None
        for fmt in common_formats:
            try:
                target_date = datetime.strptime(date_input, fmt)
                break
            except ValueError:
                continue

        if target_date is None:
            raise ValueError(
                f"Invalid date format: {date_input}. "
                f"Supported formats: MM/DD/YYYY, today, tomorrow, yesterday, +N, -N"
            )

    # Return in MM/DD/YYYY format that the website expects
    # (mypy cannot prove target_date is non-None across the branches above)
    if target_date is None:
        raise ValueError(f"Invalid date format: {date_input}.")
    return target_date.strftime("%m/%d/%Y")


# Sentinels used to push unparseable values to the end of a sort order.
_MAX_DATE = datetime.max
_MAX_MINUTES = 24 * 60 + 1


def to_iso_date(value: str) -> str:
    """Normalize a date string to ISO ``YYYY-MM-DD`` for database storage.

    ISO dates sort and range-compare correctly as text, unlike ``MM/DD/YYYY``.
    Accepts the app's usual formats; returns the input unchanged if it can't be
    parsed (so unexpected values are never silently dropped).
    """
    if not value:
        return value
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return value


def from_iso_date(value: str) -> str:
    """Format a stored ISO date back to ``MM/DD/YYYY`` for display/website use.

    Returns the input unchanged if it can't be parsed.
    """
    if not value:
        return value
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).strftime("%m/%d/%Y")
        except ValueError:
            continue
    return value


def date_sort_key(date_str: str) -> datetime:
    """Return a sortable datetime for a court date string.

    Dates are stored as ``MM/DD/YYYY`` text, which sorts incorrectly
    lexicographically. Parse to a real ``datetime`` for chronological
    ordering; unparseable values sort last.
    """
    if not date_str:
        return _MAX_DATE
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return _MAX_DATE


def time_sort_key(time_str: str) -> int:
    """Return minutes-since-midnight for a 12-hour time string.

    Time slots are stored as ``"8:00 am"`` text, which sorts incorrectly
    lexicographically (``"10:00 am"`` before ``"8:00 am"``). Convert to a
    numeric key for chronological ordering; unparseable values sort last.
    """
    if not time_str:
        return _MAX_MINUTES
    try:
        parsed = datetime.strptime(time_str.strip().lower(), "%I:%M %p")
    except ValueError:
        return _MAX_MINUTES
    return parsed.hour * 60 + parsed.minute
