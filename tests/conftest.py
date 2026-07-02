"""Shared pytest fixtures for the doral-courts test suite."""

from typing import List, Optional

import pytest

from doral_courts.core.database import Database
from doral_courts.core.db_adapter import SQLiteAdapter
from doral_courts.core.html_extractor import Court, TimeSlot


@pytest.fixture
def make_court():
    """Factory fixture for building Court objects with sensible defaults."""

    def _make(
        name: str = "DCP Tennis Court 1",
        sport_type: str = "Tennis",
        location: str = "Doral Central Park",
        capacity: str = "4",
        availability_status: str = "Available",
        date: str = "07/12/2025",
        time_slots: Optional[List[TimeSlot]] = None,
        price: Optional[str] = "$10.00",
    ) -> Court:
        if time_slots is None:
            time_slots = [
                TimeSlot("8:00 am", "9:00 am", "Available"),
                TimeSlot("9:00 am", "10:00 am", "Unavailable"),
            ]
        return Court(
            name=name,
            sport_type=sport_type,
            location=location,
            capacity=capacity,
            availability_status=availability_status,
            date=date,
            time_slots=time_slots,
            price=price,
        )

    return _make


@pytest.fixture
def db(tmp_path) -> Database:
    """A Database backed by a throwaway SQLite file in a temp directory."""
    return Database(adapter=SQLiteAdapter(db_path=str(tmp_path / "test.db")))


def build_search_page(
    court_names: List[str],
    *,
    sport: str = "Tennis",
    next_page: Optional[int] = None,
) -> str:
    """Build a minimal Doral search-results HTML page for scraper tests.

    Produces a ``frwebsearch_output_table`` containing one row per court name
    (each followed by a cart-blocks row with a single available slot), and an
    optional "next page" pagination button.
    """
    rows = []
    for name in court_names:
        rows.append(
            f"""
            <tr>
              <td class="label-cell" data-title="Facility Description">{name}</td>
              <td class="label-cell" data-title="Location Description">Doral Central Park</td>
              <td class="label-cell" data-title="Class Description">{sport}</td>
              <td class="label-cell" data-title="Capacity">4</td>
              <td class="label-cell" data-title="Price">$10.00</td>
            </tr>
            <tr>
              <td class="cart-blocks">
                <a class="cart-button success" data-tooltip="Book Now">8:00 am - 9:00 am</a>
              </td>
            </tr>
            """
        )

    next_button = ""
    if next_page is not None:
        next_button = f'<button data-click-set-value="{next_page}">Next</button>'

    return f"""
    <html><head><title>Search</title></head><body>
      <table id="frwebsearch_output_table"><tbody>
        {"".join(rows)}
      </tbody></table>
      {next_button}
    </body></html>
    """
