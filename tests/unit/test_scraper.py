"""Tests for the scraper's pagination and duplicate-detection control flow.

The HTTP layer is mocked so these tests never hit the network.
"""

from unittest.mock import MagicMock

import pytest

from doral_courts.core.scraper import Scraper, classify_anti_bot_response

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


class TestAntiBotClassification:
    """The scraper must distinguish rejections a user can act on.

    An edge-level WAF/IP block is unfixable in code, while a lost JavaScript
    challenge is the one case where a different bypass library would help.
    Collapsing both into one vague message sends users chasing the wrong fix.
    """

    WAF_BODY = (
        "<html><head><title>Attention Required! | Cloudflare</title></head>"
        "<body>Sorry, you have been blocked</body></html>"
    )
    CHALLENGE_BODY = (
        "<html><body>Checking your browser before accessing"
        "<script>cf_chl_opt</script></body></html>"
    )

    def test_success_is_not_a_block(self):
        assert classify_anti_bot_response(200, "<html>ok</html>") is None
        assert classify_anti_bot_response(302, "") is None

    def test_waf_block_detected(self):
        block = classify_anti_bot_response(403, self.WAF_BODY)
        assert block is not None
        assert block.kind == "waf"
        # The message must tell the user this is not solvable by better code.
        assert "different network" in block.message

    def test_challenge_is_not_confused_with_waf(self):
        block = classify_anti_bot_response(403, self.CHALLENGE_BODY)
        assert block is not None
        assert block.kind == "challenge"

    def test_rate_limit_detected(self):
        block = classify_anti_bot_response(429, "slow down")
        assert block is not None
        assert block.kind == "rate_limit"

    def test_waf_takes_precedence_over_rate_limit_status(self):
        # A WAF block served with a 429 is still a WAF block: the body is the
        # stronger signal, and the advice differs.
        block = classify_anti_bot_response(429, self.WAF_BODY)
        assert block is not None
        assert block.kind == "waf"

    def test_unrecognised_error_still_classified(self):
        block = classify_anti_bot_response(500, "<html>oops</html>")
        assert block is not None
        assert block.kind == "http"
        assert "500" in block.message

    def test_empty_body_does_not_crash(self):
        block = classify_anti_bot_response(403, "")
        assert block is not None
        assert block.kind == "http"


class TestScraperRecordsBlocks:
    def test_session_failure_records_waf_block(self, monkeypatch):
        s = Scraper()
        s.session.get = MagicMock(
            return_value=FakeResponse(
                TestAntiBotClassification.WAF_BODY, status_code=403
            )
        )
        assert s._initialize_session() is False
        assert s.last_block is not None
        assert s.last_block.kind == "waf"

    def test_successful_session_clears_block(self, monkeypatch):
        s = Scraper()
        s.session.get = MagicMock(return_value=FakeResponse("<html>ok</html>"))
        assert s._initialize_session() is True
        assert s.last_block is None

    def test_native_interpreter_is_pinned(self):
        # Guards against a dependency swap silently moving us onto js2py,
        # which is broken on Python 3.13+.
        assert Scraper().session.interpreter == "native"
