"""Tests for the display modules (Rich table/list rendering)."""

from doral_courts.display.detailed import (
    display_detailed_court_data,
    display_time_slots_summary,
)
from doral_courts.display.lists import display_courts_list, display_locations_list
from doral_courts.display.tables import (
    display_available_slots_table,
    display_courts_table,
)


class TestTables:
    def test_courts_table_renders_names(self, make_court, capsys):
        courts = [
            make_court(name="DCP Tennis Court 1", sport_type="Tennis"),
            make_court(name="DLP Pickle Court 2", sport_type="Pickleball"),
        ]
        display_courts_table(courts)
        out = capsys.readouterr().out
        assert "DCP Tennis Court 1" in out

    def test_courts_table_empty(self, capsys):
        # Renders the table header/title without rows and without raising.
        display_courts_table([])
        assert "Doral Courts Availability" in capsys.readouterr().out

    def test_courts_table_marks_favorites(self, make_court, capsys):
        courts = [make_court(name="Fav Court 1")]
        display_courts_table(courts, favorite_court_names={"Fav Court 1"})
        # Should render without error and include the court.
        assert "Fav Court 1" in capsys.readouterr().out

    def test_available_slots_table_orders_chronologically(self, make_court, capsys):
        from doral_courts.core.html_extractor import TimeSlot

        court = make_court(
            name="Court Z",
            time_slots=[
                TimeSlot("10:00 am", "11:00 am", "Available"),
                TimeSlot("8:00 am", "9:00 am", "Available"),
            ],
        )
        display_available_slots_table([court], "07/12/2025")
        out = capsys.readouterr().out
        # 8:00 am should be rendered before 10:00 am (chronological sort).
        assert out.index("8:00 am") < out.index("10:00 am")

    def test_available_slots_table_none_available(self, make_court, capsys):
        from doral_courts.core.html_extractor import TimeSlot

        court = make_court(time_slots=[TimeSlot("8:00 am", "9:00 am", "Unavailable")])
        display_available_slots_table([court], "07/12/2025")
        assert "No available time slots" in capsys.readouterr().out


class TestLists:
    def test_courts_list(self, make_court, capsys):
        display_courts_list([make_court(name="Court A")])
        assert "Court A" in capsys.readouterr().out

    def test_locations_list(self, make_court, capsys):
        display_locations_list([make_court(location="Doral Central Park")])
        assert "Doral Central Park" in capsys.readouterr().out


class TestDetailed:
    def test_detailed_view(self, make_court, capsys):
        display_detailed_court_data([make_court(name="Court D")], "http://src")
        assert "Court D" in capsys.readouterr().out

    def test_time_slots_summary(self, make_court, capsys):
        display_time_slots_summary([make_court()], "http://src")
        # Renders without raising and produces output.
        assert capsys.readouterr().out.strip() != ""
