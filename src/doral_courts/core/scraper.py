from datetime import datetime, time
from typing import List, Optional

import cloudscraper
import requests
from bs4 import BeautifulSoup

from ..utils.logger import get_logger
from .html_extractor import Court, CourtAvailabilityHTMLExtractor

logger = get_logger(__name__)


class Scraper:
    """
    Web scraper for the Doral courts reservation system.

    Handles fetching court availability data from the Doral reservation website,
    including bypassing Cloudflare protection and parsing the returned HTML.
    Uses cloudscraper to handle anti-bot protection and maintains session state.

    Features:
        - Cloudflare bypass using cloudscraper
        - Session management with proper headers
        - Date and sport filtering
        - HTML extraction with error handling
        - URL tracking for debugging

    Attributes:
        base_url: Main search endpoint for court data
        home_url: Homepage for session initialization
        session: cloudscraper session for making requests
        html_extractor: HTML parser for court data
        last_request_urls: Recent request URLs for debugging

    Usage:
        scraper = Scraper()
        courts = scraper.fetch_courts(date="07/12/2025", sport_filter="tennis")
    """

    def __init__(self):
        """
        Initialize scraper with cloudscraper session and configuration.

        Sets up the web scraper with Cloudflare bypass capabilities using
        cloudscraper. Configures browser headers and creates session for
        making authenticated requests to the Doral reservation system.

        Configuration:
            - Chrome browser simulation for compatibility
            - Darwin platform for macOS compatibility
            - Comprehensive headers for legitimate browser behavior
            - Cloudflare protection bypass enabled
        """
        self.base_url = "https://fldoralweb.myvscloud.com/webtrac/web/search.html"
        self.home_url = "https://fldoralweb.myvscloud.com/webtrac/web/splash.html"
        self.html_extractor = CourtAvailabilityHTMLExtractor()
        self.last_request_urls = []  # Store actual URLs from recent requests

        # Create cloudscraper session to bypass Cloudflare protection
        self.session = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "darwin", "desktop": True},
            debug=False,  # Disable debug output
        )

        # Additional headers for better compatibility (let cloudscraper handle encoding)
        self.session.headers.update(
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "max-age=0",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            }
        )

        logger.debug(
            "Initialized Scraper with cloudscraper and base URL: %s", self.base_url
        )

    def _initialize_session(self):
        """
        Initialize session by visiting the home page to get cookies and tokens.

        Performs initial request to the Doral homepage to establish session
        cookies and handle any Cloudflare challenges. This is required before
        making requests to the search endpoints.

        Returns:
            bool: True if session initialization successful, False otherwise

        Error Handling:
            - Logs detailed error information for debugging
            - Returns False on failure but doesn't raise exceptions
            - Handles timeout and connection errors gracefully

        Side Effects:
            - Updates session cookies
            - May solve Cloudflare challenges
            - Logs session status for debugging
        """
        logger.debug("Initializing cloudscraper session")

        try:
            # cloudscraper should automatically handle Cloudflare challenges
            # Just try to access the main page
            logger.debug("Attempting to access home page with cloudscraper")
            response = self.session.get(self.home_url, timeout=30)
            logger.debug("Home page response: %d", response.status_code)

            # Add essential cookies if they weren't set automatically
            if "_CookiesEnabled" not in self.session.cookies:
                self.session.cookies.set("_CookiesEnabled", "Yes")
            if "_mobile" not in self.session.cookies:
                self.session.cookies.set("_mobile", "no")

            logger.debug("Session cookies: %s", list(self.session.cookies.keys()))

            # Consider any non-error status as success since cloudscraper handles challenges
            if response.status_code < 500:
                logger.info("Session initialized successfully with cloudscraper")
                return True
            else:
                logger.warning(
                    "Server error during session initialization: %d",
                    response.status_code,
                )
                return False

        except Exception as e:
            logger.error("Failed to initialize session with cloudscraper: %s", e)
            return False

    def _get_csrf_token(self) -> str:
        """Extract CSRF token from the search page."""
        logger.debug("Fetching CSRF token from search page")

        try:
            response = self.session.get(self.base_url, timeout=30)
            logger.debug("CSRF token fetch response: %d", response.status_code)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                csrf_input = soup.find("input", {"name": "_csrf_token"})

                if csrf_input and csrf_input.get("value"):
                    token = csrf_input["value"]
                    logger.debug("Found CSRF token: %s...", token[:20])
                    return token
                else:
                    logger.warning("CSRF token not found in page")
                    return ""
            else:
                logger.warning(
                    "Failed to fetch CSRF token page, status: %d", response.status_code
                )
                return ""

        except Exception as e:
            logger.error("Failed to fetch CSRF token: %s", e)
            return ""

    def _build_search_params(
        self, date: str = None, begin_time: str = "08:00 am", page: int = 1
    ) -> dict:
        """Build search parameters for the court availability request."""
        if not date:
            from datetime import datetime

            date = datetime.now().strftime("%m/%d/%Y")
            logger.debug("Using current date: %s", date)
        else:
            logger.debug("Using provided date: %s", date)

        logger.debug("Building search params for page %d, time %s", page, begin_time)
        csrf_token = self._get_csrf_token()

        params = {
            "Action": "Start",
            "SubAction": "",
            "_csrf_token": csrf_token,
            "date": date,
            "begintime": begin_time,
            "type": ["Pickleball Court", "Tennis Court"],
            "subtype": "",
            "category": "",
            "features": "",
            "keyword": "",
            "keywordoption": "Match One",
            "blockstodisplay": "50",
            "frheadcount": "0",
            "primarycode": "",
            "features1": "",
            "features2": "",
            "features3": "",
            "features4": "",
            "features5": "",
            "features6": "",
            "features7": "",
            "features8": "",
            "display": "Detail",
            "search": "yes",
            "page": str(page),
            "module": "fr",
            "multiselectlist_value": "",
            "frwebsearch_buttonsearch": "yes",
        }

        logger.debug("Built search params with %d parameters", len(params))
        return params

    def fetch_courts(self, date: str = None, sport_filter: str = None) -> List[Court]:
        """Fetch court availability data from the website."""
        courts, _ = self.fetch_courts_with_html(date, sport_filter)
        return courts

    def fetch_courts_with_html(
        self, date: str = None, sport_filter: str = None
    ) -> tuple[List[Court], str]:
        """Fetch court availability data from the website and return both courts and HTML."""
        logger.info("Starting court data fetch from website")
        logger.debug(
            "Fetch parameters - Date: %s, Sport filter: %s", date, sport_filter
        )

        # Initialize session first
        if not self._initialize_session():
            logger.error("Failed to initialize session with website")
            return [], ""

        all_courts = []
        all_html_content = []
        page = 1
        self.last_request_urls = []  # Reset for this fetch operation

        try:
            while True:
                logger.debug("Fetching page %d", page)
                params = self._build_search_params(date=date, page=page)

                # Update headers for this specific request
                headers = {
                    "Referer": self.base_url,
                    "Sec-Fetch-Site": "same-origin",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Dest": "document",
                }

                logger.debug("Making request to %s", self.base_url)
                response = self.session.get(
                    self.base_url, params=params, headers=headers
                )

                # Capture the actual URL with query parameters
                self.last_request_urls.append(response.url)
                logger.debug("Actual request URL: %s", response.url)

                if response.status_code == 200:
                    logger.debug(
                        "Successfully received response (status: %d, size: %d bytes)",
                        response.status_code,
                        len(response.content),
                    )

                    # Store HTML content for potential saving
                    html_content = response.text
                    all_html_content.append(html_content)

                    # Debug: save HTML to see what we're getting
                    if logger.isEnabledFor(10):  # DEBUG level
                        try:
                            with open(
                                f"debug_page_{page}.html",
                                "w",
                                encoding="utf-8",
                                errors="replace",
                            ) as f:
                                f.write(html_content)
                            logger.debug(
                                "Saved HTML content to debug_page_%d.html", page
                            )
                        except Exception as e:
                            logger.debug("Could not save HTML debug file: %s", e)

                    # Use response.text instead of response.content for better encoding handling
                    soup = BeautifulSoup(html_content, "html.parser")
                    courts = self.html_extractor.parse_court_data(soup)

                    if not courts:
                        logger.debug(
                            "No courts found on page %d, stopping pagination", page
                        )
                        break

                    logger.debug("Found %d courts on page %d", len(courts), page)

                    # Check for duplicates - if this page returns the same courts as before, stop
                    existing_court_names = set(court.name for court in all_courts)
                    new_court_names = set(court.name for court in courts)
                    duplicate_count = len(
                        new_court_names.intersection(existing_court_names)
                    )

                    if duplicate_count > 0 and page > 1:
                        logger.warning(
                            "Found %d duplicate courts on page %d (%.1f%% duplicates)",
                            duplicate_count,
                            page,
                            (duplicate_count / len(courts)) * 100,
                        )

                        # If more than 50% of courts are duplicates, likely we're getting repeated data
                        if duplicate_count / len(courts) > 0.5:
                            logger.warning(
                                "Page %d contains mostly duplicate data (%.1f%%), stopping pagination",
                                page,
                                (duplicate_count / len(courts)) * 100,
                            )
                            break

                    # Only add new courts (deduplicate)
                    new_courts = [
                        court
                        for court in courts
                        if court.name not in existing_court_names
                    ]
                    all_courts.extend(new_courts)

                    if new_courts:
                        logger.debug(
                            "Added %d new courts from page %d (skipped %d duplicates)",
                            len(new_courts),
                            page,
                            len(courts) - len(new_courts),
                        )
                    else:
                        logger.debug(
                            "No new courts found on page %d, all were duplicates", page
                        )

                    # Check if there's a next page
                    # Look for pagination buttons with higher page numbers
                    current_page = page
                    next_page_value = str(current_page + 1)

                    # Look for button with data-click-set-value pointing to next page
                    next_page_button = soup.find(
                        "button", {"data-click-set-value": next_page_value}
                    )

                    # Also check for "Go To Last Page" button to see if more pages exist
                    last_page_button = soup.find("button", class_="paging__lastpage")

                    if not next_page_button and not last_page_button:
                        logger.debug("No next page button found, stopping pagination")
                        break

                    # If we have a next page button, continue
                    if next_page_button:
                        logger.debug(
                            "Found next page button for page %s", next_page_value
                        )
                    # If no direct next page button but there's a last page button, check if we can continue
                    elif last_page_button:
                        last_page_value = last_page_button.get(
                            "data-click-set-value", "1"
                        )
                        try:
                            max_page = int(last_page_value)
                            if current_page >= max_page:
                                logger.debug(
                                    "Already at last page (%d), stopping pagination",
                                    max_page,
                                )
                                break
                            else:
                                logger.debug(
                                    "Can continue to page %d (last page is %d)",
                                    current_page + 1,
                                    max_page,
                                )
                        except (ValueError, TypeError):
                            logger.debug(
                                "Could not determine last page number, stopping pagination"
                            )
                            break

                    page += 1

                elif response.status_code == 403:
                    logger.error(
                        "Received 403 Forbidden - website is blocking automated requests"
                    )
                    logger.error(
                        "The website has anti-bot protection that prevents access"
                    )
                    break
                else:
                    logger.error("Website returned status %d", response.status_code)
                    break

        except requests.RequestException as e:
            logger.error("Network error while fetching from website: %s", e)

        # Combine all HTML content
        combined_html = "\n\n<!-- PAGE BREAK -->\n\n".join(all_html_content)

        if all_courts:
            logger.info(
                "Successfully fetched %d total courts from %d pages",
                len(all_courts),
                page,
            )

            # Apply sport filter if specified
            if sport_filter:
                original_count = len(all_courts)
                all_courts = [
                    court
                    for court in all_courts
                    if court.sport_type.lower() == sport_filter.lower()
                ]
                logger.debug(
                    "Applied sport filter '%s': %d -> %d courts",
                    sport_filter,
                    original_count,
                    len(all_courts),
                )

            logger.info("Returning %d courts from website", len(all_courts))
        else:
            logger.warning("No court data could be retrieved from website")

        return all_courts, combined_html

    def get_last_request_url(self) -> str:
        """Get the most recent request URL with query parameters."""
        if self.last_request_urls:
            return str(self.last_request_urls[-1])
        return self.base_url

    def get_all_request_urls(self) -> list:
        """Get all request URLs from the last fetch operation."""
        return [str(url) for url in self.last_request_urls]
