from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List
from datetime import datetime
from logger import get_logger

logger = get_logger(__name__)

@dataclass
class TimeSlot:
    """
    Represents a time slot for court reservations.

    Attributes:
        start_time: Start time in 12-hour format (e.g., "8:00 am")
        end_time: End time in 12-hour format (e.g., "9:00 am")
        status: Availability status ("Available" or "Unavailable")

    Example:
        slot = TimeSlot("8:00 am", "9:00 am", "Available")
    """
    start_time: str
    end_time: str
    status: str  # "Available" or "Unavailable"

@dataclass
class Court:
    """
    Represents a court with its availability information and time slots.

    Attributes:
        name: Court name (e.g., "DCP Tennis Court 1")
        sport_type: Type of sport ("Tennis" or "Pickleball")
        location: Location name (e.g., "Doral Central Park")
        capacity: Maximum number of players (e.g., "3", "4")
        availability_status: Overall status ("Available", "Fully Booked", "No Schedule")
        date: Date in MM/DD/YYYY format
        time_slots: List of TimeSlot objects for this court
        price: Price information (optional, e.g., "$10.00")

    Example:
        court = Court(
            name="DCP Tennis Court 1",
            sport_type="Tennis",
            location="Doral Central Park",
            capacity="3",
            availability_status="Available",
            date="07/12/2025",
            time_slots=[TimeSlot("8:00 am", "9:00 am", "Available")],
            price="$10.00"
        )
    """
    name: str
    sport_type: str
    location: str
    capacity: str
    availability_status: str
    date: str
    time_slots: List[TimeSlot]
    price: str = None

    @property
    def time_slot(self) -> str:
        """
        Legacy property for compatibility with older code.

        Returns:
            String representation of available time slots in format "X/Y available"
            where X is available slots and Y is total slots.
            Returns "No time slots" if no slots exist.

        Example:
            "3/5 available" or "No time slots"
        """
        if not self.time_slots:
            return "No time slots"
        available_count = sum(1 for slot in self.time_slots if slot.status == "Available")
        total_count = len(self.time_slots)
        return f"{available_count}/{total_count} available"

class CourtAvailabilityHTMLExtractor:
    """
    HTML extractor for parsing court availability data from Doral reservation system.

    This class handles the parsing of complex HTML structures from the Doral courts
    reservation website, extracting court information, time slots, and availability
    status. It handles multiple table formats and varying HTML structures.

    The extractor processes:
    - Court basic information (name, sport, location, capacity, price)
    - Time slot availability and booking status
    - Overall court availability status
    - Date information and formatting

    Usage:
        extractor = CourtAvailabilityHTMLExtractor()
        courts = extractor.parse_court_data(soup)
    """

    def parse_court_data(self, soup: BeautifulSoup) -> List[Court]:
        """
        Parse court data from the HTML response.

        Extracts court information from HTML containing multiple tables with court
        data. Each table may contain multiple courts, and each court may have
        associated time slots in subsequent rows.

        Args:
            soup: BeautifulSoup object containing parsed HTML from Doral website

        Returns:
            List of Court objects with extracted information and time slots

        Raises:
            Exception: Logs warnings for parsing errors but continues processing

        HTML Structure Expected:
            - Tables with id="frwebsearch_output_table"
            - Rows with class="label-cell" containing court data
            - Time slot data in rows with class="cart-blocks"

        Example:
            soup = BeautifulSoup(html_content, 'html.parser')
            courts = extractor.parse_court_data(soup)
            print(f"Found {len(courts)} courts")
        """
        logger.debug("Starting court data parsing")
        courts = []

        # Debug: let's examine the HTML structure
        logger.debug("HTML title: %s", soup.title.string if soup.title else "No title")

        # Look for ALL tables with court data (there are multiple tables, each with the same ID)
        court_tables = soup.find_all('table', id='frwebsearch_output_table')
        if not court_tables:
            logger.warning("Could not find any frwebsearch_output_table")
            return courts

        logger.debug("Found %d frwebsearch_output_tables", len(court_tables))

        # Process each table separately
        for table_index, court_table in enumerate(court_tables):
            logger.debug("Processing table %d/%d", table_index + 1, len(court_tables))

            # Find all rows in the tbody
            tbody = court_table.find('tbody')
            if not tbody:
                logger.debug("Could not find tbody in court table %d, skipping", table_index + 1)
                continue

            # Get all rows, but filter out cart-blocks rows
            all_rows = tbody.find_all('tr')
            court_rows = [row for row in all_rows if not row.find('td', class_='cart-blocks')]

            logger.debug("Found %d court data rows in table %d", len(court_rows), table_index + 1)

            for i, row in enumerate(court_rows):
                logger.debug("Processing court row %d/%d in table %d", i + 1, len(court_rows), table_index + 1)
                try:
                    # Extract data from label-cell elements using data-title attributes
                    cells = row.find_all('td', class_='label-cell')

                    if len(cells) < 4:
                        logger.debug("Row %d has insufficient cells (%d), skipping", i + 1, len(cells))
                        continue

                    # Extract date from dateblock or data-title="Date"
                    date_cell = row.find('td', {'data-title': 'Date'})
                    if date_cell:
                        # Try to extract from dateblock
                        dateblock = date_cell.find('span', class_='dateblock')
                        if dateblock and dateblock.get('data-tooltip'):
                            date = dateblock['data-tooltip']
                        else:
                            date = date_cell.get_text(strip=True)
                    else:
                        date = datetime.now().strftime("%m/%d/%Y")

                    # Extract facility description (court name)
                    name_cell = row.find('td', {'data-title': 'Facility Description'})
                    name = name_cell.get_text(strip=True) if name_cell else "Unknown Court"

                    # Extract location description
                    location_cell = row.find('td', {'data-title': 'Location Description'})
                    location = location_cell.get_text(strip=True) if location_cell else "Unknown Location"

                    # Extract class description (sport type)
                    class_cell = row.find('td', {'data-title': 'Class Description'})
                    class_description = class_cell.get_text(strip=True) if class_cell else ""

                    # Determine sport type from class description or name
                    sport_type = "Tennis" if "tennis" in class_description.lower() or "tennis" in name.lower() else "Pickleball"

                    # Extract capacity
                    capacity_cell = row.find('td', {'data-title': 'Capacity'})
                    capacity = capacity_cell.get_text(strip=True) if capacity_cell else "N/A"

                    # Extract price
                    price_cell = row.find('td', {'data-title': 'Price'})
                    price = price_cell.get_text(strip=True) if price_cell else None

                    # Extract time slots from the cart-blocks section
                    time_slots = self._extract_time_slots(row)

                    # Determine overall availability status based on time slots
                    if time_slots:
                        available_slots = [slot for slot in time_slots if slot.status == "Available"]
                        if available_slots:
                            availability_status = "Available"
                        else:
                            availability_status = "Fully Booked"
                    else:
                        availability_status = "No Schedule"

                    court = Court(
                        name=name,
                        sport_type=sport_type,
                        location=location,
                        capacity=capacity,
                        availability_status=availability_status,
                        date=date,
                        time_slots=time_slots,
                        price=price
                    )

                    courts.append(court)
                    logger.debug("Successfully parsed court: %s (%s) at %s on %s", name, sport_type, location, date)

                except Exception as e:
                    logger.warning("Error parsing court row %d in table %d: %s", i + 1, table_index + 1, e)
                    continue

        logger.info("Parsed %d courts from HTML", len(courts))
        return courts

    def _extract_time_slots(self, court_row) -> List[TimeSlot]:
        """
        Extract time slots from the cart-blocks section following a court row.

        Parses the HTML structure containing booking buttons to extract time slot
        information including start/end times and availability status. Handles
        different button styles for available and unavailable slots.

        Args:
            court_row: BeautifulSoup TR element containing court information

        Returns:
            List of TimeSlot objects extracted from the cart-blocks section.
            Returns empty list if no time slots found or parsing fails.

        HTML Structure Expected:
            - Next sibling TR element contains TD with class="cart-blocks"
            - Cart-blocks contains A elements with class="cart-button"
            - Available slots: class="success" + data-tooltip="Book Now"
            - Unavailable slots: class="error" + nested span elements

        Time Format Handling:
            - Parses "HH:MM am/pm - HH:MM am/pm" format
            - Handles extra whitespace and formatting variations
            - Falls back gracefully for malformed time strings

        Example:
            time_slots = self._extract_time_slots(court_row)
            for slot in time_slots:
                print(f"{slot.start_time} - {slot.end_time}: {slot.status}")
        """
        time_slots = []

        # Find the next row which should contain cart-blocks
        next_row = court_row.find_next_sibling('tr')
        if not next_row:
            logger.debug("No next row found after court row")
            return time_slots

        cart_blocks = next_row.find('td', class_='cart-blocks')
        if not cart_blocks:
            logger.debug("No cart-blocks found in next row")
            return time_slots

        # Find all cart-button elements (time slot buttons)
        cart_buttons = cart_blocks.find_all('a', class_='cart-button')
        logger.debug("Found %d time slot buttons", len(cart_buttons))

        for button in cart_buttons:
            try:
                button_classes = button.get('class', [])
                button_tooltip = button.get('data-tooltip', '')

                # Check if this is an available slot
                # Available slots have 'success' class and 'Book Now' tooltip
                is_available = ('success' in button_classes and
                               'Book Now' in button_tooltip)

                # Extract time range text
                if is_available:
                    # Available slots have time directly in button text
                    time_range_text = button.get_text(strip=True)
                else:
                    # Unavailable slots have time in first span
                    time_spans = button.find_all('span')
                    if len(time_spans) < 1:
                        continue
                    time_range_text = time_spans[0].get_text(strip=True)

                # Parse time range (e.g., "8:00 am - 9:00 am" or " 2:00 pm -  3:00 pm")
                if ' - ' in time_range_text:
                    start_time, end_time = time_range_text.split(' - ', 1)
                    start_time = start_time.strip()
                    end_time = end_time.strip()
                else:
                    # Fallback if format is different
                    start_time = time_range_text.strip()
                    end_time = ""

                # Determine status based on button characteristics
                if is_available:
                    status = "Available"
                else:
                    status = "Unavailable"

                time_slot = TimeSlot(
                    start_time=start_time,
                    end_time=end_time,
                    status=status
                )

                time_slots.append(time_slot)
                logger.debug("Parsed time slot: %s - %s (%s)", start_time, end_time, status)

            except Exception as e:
                logger.warning("Error parsing time slot: %s", e)
                continue

        logger.debug("Extracted %d time slots", len(time_slots))
        return time_slots
