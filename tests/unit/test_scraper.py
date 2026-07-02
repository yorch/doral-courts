"""Tests for the scraper's pagination and duplicate-detection control flow.

The HTTP layer is mocked so these tests never hit the network.
"""

from unittest.mock import MagicMock

import pytest

from doral_courts.core.scraper import Scraper

from ..conftest import build_search_page


class FakeResponse:
    def __init__(self, html: str, status_code: int = 200, url: str = "http://test"):
        self.status_code = status_code
        self.text = html
        self.content = html.encode("utf-8")
        self.url = url


@pytest.fixture
def scraper(monkeypatch):
    s = Scraper()
    # Bypass the network-dependent session setup and token fetch.
    monkeypatch.setattr(s, "_initialize_session", lambda: True)
    monkeypatch.setattr(s, "_get_csrf_token", lambda: "test-token")
    return s


def test_single_page_returns_all_courts(scraper):
    scraper.session.get = MagicMock(
        return_value=FakeResponse(build_search_page(["Court A", "Court B"]))
    )
    courts = scraper.fetch_courts(date="07/12/2025")
    assert {c.name for c in courts} == {"Court A", "Court B"}
    # No next-page button => exactly one request.
    assert scraper.session.get.call_count == 1


def test_pagination_follows_next_button(scraper):
    scraper.session.get = MagicMock(
        side_effect=[
            FakeResponse(build_search_page(["Court A"], next_page=2)),
            FakeResponse(build_search_page(["Court B"])),
        ]
    )
    courts = scraper.fetch_courts(date="07/12/2025")
    assert {c.name for c in courts} == {"Court A", "Court B"}
    assert scraper.session.get.call_count == 2


def test_duplicate_page_stops_pagination(scraper):
    # Page 2 repeats page 1's court => mostly-duplicate => stop, no infinite loop.
    scraper.session.get = MagicMock(
        side_effect=[
            FakeResponse(build_search_page(["Court A"], next_page=2)),
            FakeResponse(build_search_page(["Court A"], next_page=3)),
            FakeResponse(build_search_page(["Court A"], next_page=4)),
        ]
    )
    courts = scraper.fetch_courts(date="07/12/2025")
    assert [c.name for c in courts] == ["Court A"]
    # Stopped at page 2 on duplicates rather than chasing next_page forever.
    assert scraper.session.get.call_count == 2


def test_empty_results_stops(scraper):
    scraper.session.get = MagicMock(return_value=FakeResponse(build_search_page([])))
    courts = scraper.fetch_courts(date="07/12/2025")
    assert courts == []


def test_sport_filter_applied(scraper):
    scraper.session.get = MagicMock(
        return_value=FakeResponse(build_search_page(["Tennis A"], sport="Tennis"))
    )
    tennis = scraper.fetch_courts(date="07/12/2025", sport_filter="tennis")
    assert [c.name for c in tennis] == ["Tennis A"]
    other = scraper.fetch_courts(date="07/12/2025", sport_filter="pickleball")
    assert other == []


def test_failed_session_returns_empty(monkeypatch):
    s = Scraper()
    monkeypatch.setattr(s, "_initialize_session", lambda: False)
    s.session.get = MagicMock()
    courts, html = s.fetch_courts_with_html(date="07/12/2025")
    assert courts == []
    assert html == ""
    s.session.get.assert_not_called()
