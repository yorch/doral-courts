"""Smoke tests for cache-reading commands (stats, history, cleanup, analyze,
favorites) against an isolated temp database and config.
"""

from datetime import datetime

import pytest
from click.testing import CliRunner

from doral_courts.cli.main import cli
from doral_courts.core.database import Database
from doral_courts.core.html_extractor import Court, TimeSlot

# Commands like `history` default to today's date; seed with today so the
# cached row is visible to date-filtered queries.
TODAY = datetime.now().strftime("%m/%d/%Y")


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """Isolate HOME (config) and CWD (default SQLite path) to a temp dir."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)


def _seed() -> None:
    Database().insert_courts(
        [
            Court(
                name="DCP Tennis Court 1",
                sport_type="Tennis",
                location="Doral Central Park",
                capacity="4",
                availability_status="Available",
                date=TODAY,
                time_slots=[TimeSlot("8:00 am", "9:00 am", "Available")],
                price="$10.00",
            )
        ]
    )


class TestStats:
    def test_empty(self, runner):
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0, result.output

    def test_with_data(self, runner):
        _seed()
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0, result.output
        assert "Tennis" in result.output


class TestHistory:
    def test_empty(self, runner):
        result = runner.invoke(cli, ["history"])
        assert result.exit_code == 0, result.output

    def test_with_data(self, runner):
        _seed()
        result = runner.invoke(cli, ["history"])
        assert result.exit_code == 0, result.output
        # Column values may be truncated by table width; check a stable prefix.
        assert "DCP" in result.output


class TestCleanup:
    def test_runs_and_keeps_recent(self, runner):
        _seed()
        result = runner.invoke(cli, ["cleanup", "--days", "7"])
        assert result.exit_code == 0, result.output
        assert "Removed 0 records" in result.output


class TestAnalyze:
    def test_empty_reports_no_data(self, runner):
        result = runner.invoke(cli, ["analyze"])
        assert result.exit_code == 0, result.output


class TestFavorites:
    def test_add_list_remove(self, runner):
        add = runner.invoke(cli, ["favorites", "add", "DCP Tennis Court 1"])
        assert add.exit_code == 0, add.output

        listing = runner.invoke(cli, ["favorites", "list"])
        assert listing.exit_code == 0, listing.output
        assert "DCP Tennis Court 1" in listing.output

        remove = runner.invoke(cli, ["favorites", "remove", "DCP Tennis Court 1"])
        assert remove.exit_code == 0, remove.output
