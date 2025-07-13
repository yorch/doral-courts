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
        target_date = datetime.now() + timedelta(days=days_offset)
    elif re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", date_input):
        # Handle MM/DD/YYYY format - validate it
        try:
            target_date = datetime.strptime(date_input, "%m/%d/%Y")
        except ValueError:
            raise ValueError(
                f"Invalid date format: {date_input}. Use MM/DD/YYYY format."
            )
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
    return target_date.strftime("%m/%d/%Y")
