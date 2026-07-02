"""Smoke tests for the CLI commands using Click's CliRunner.

External I/O (scraping, database) is mocked so these never hit the network.
"""

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from doral_courts.cli.main import cli
from doral_courts.core.html_extractor import Court, TimeSlot


@pytest.fixture
def runner():
    return CliRunner()


def _sample_court() -> Court:
    return Court(
        name="DCP Tennis Court 1",
        sport_type="Tennis",
        location="Doral Central Park",
        capacity="4",
        availability_status="Available",
        date="07/12/2025",
        time_slots=[TimeSlot("8:00 am", "9:00 am", "Available")],
        price="$10.00",
    )


class FakeScraper:
    """Stand-in for Scraper that returns canned data without network access."""

    courts_to_return: list = []

    def __init__(self):
        pass

    def fetch_courts(self, date=None, sport_filter=None):
        return list(self.courts_to_return)

    def fetch_courts_with_html(self, date=None, sport_filter=None):
        return list(self.courts_to_return), "<html></html>"

    def get_last_request_url(self):
        return "http://test/search"


@pytest.fixture
def mock_io(monkeypatch, tmp_path):
    """Patch the scraper and database used by the shared fetch helper, and
    isolate config writes to a temp HOME."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("doral_courts.cli._shared.Database", MagicMock())
    monkeypatch.setattr("doral_courts.cli._shared.Scraper", FakeScraper)
    return FakeScraper


def test_top_level_help(runner):
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


@pytest.mark.parametrize(
    "command",
    [
        "list",
        "stats",
        "slots",
        "data",
        "cleanup",
        "history",
        "watch",
        "monitor",
        "analyze",
        "list-available-slots",
        "list-courts",
        "list-locations",
        "favorites",
        "query",
    ],
)
def test_command_help_is_wired(runner, command):
    """Every registered command should expose --help (catches wiring errors)."""
    result = runner.invoke(cli, [command, "--help"])
    assert result.exit_code == 0, result.output
    assert "Usage" in result.output


def test_list_invalid_date_reports_error(runner):
    result = runner.invoke(cli, ["list", "--date", "definitely-not-a-date"])
    assert result.exit_code == 0
    assert "Error" in result.output


def test_list_no_data_message(runner, mock_io):
    mock_io.courts_to_return = []
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "Unable to fetch" in result.output


def test_list_success_displays_court(runner, mock_io):
    mock_io.courts_to_return = [_sample_court()]
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "Tennis Court 1" in result.output
