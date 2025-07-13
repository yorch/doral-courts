import unittest
from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup

from doral_courts.core.html_extractor import (Court,
                                              CourtAvailabilityHTMLExtractor,
                                              TimeSlot)


class TestCourtAvailabilityHTMLExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = CourtAvailabilityHTMLExtractor()

    def test_time_slot_creation(self):
        """Test TimeSlot dataclass creation."""
        slot = TimeSlot(start_time="8:00 am", end_time="9:00 am", status="Available")
        self.assertEqual(slot.start_time, "8:00 am")
        self.assertEqual(slot.end_time, "9:00 am")
        self.assertEqual(slot.status, "Available")

    def test_court_creation_with_time_slots(self):
        """Test Court dataclass creation with time slots."""
        time_slots = [
            TimeSlot("8:00 am", "9:00 am", "Available"),
            TimeSlot("9:00 am", "10:00 am", "Unavailable"),
        ]

        court = Court(
            name="Test Court",
            sport_type="Tennis",
            location="Test Location",
            capacity="3",
            availability_status="Available",
            date="07/11/2025",
            time_slots=time_slots,
            price="$10.00",
        )

        self.assertEqual(court.name, "Test Court")
        self.assertEqual(len(court.time_slots), 2)
        self.assertEqual(court.time_slot, "1/2 available")

    def test_court_time_slot_property_no_slots(self):
        """Test time_slot property when no time slots are available."""
        court = Court(
            name="Test Court",
            sport_type="Tennis",
            location="Test Location",
            capacity="3",
            availability_status="No Schedule",
            date="07/11/2025",
            time_slots=[],
        )

        self.assertEqual(court.time_slot, "No time slots")

    def test_court_time_slot_property_all_unavailable(self):
        """Test time_slot property when all slots are unavailable."""
        time_slots = [
            TimeSlot("8:00 am", "9:00 am", "Unavailable"),
            TimeSlot("9:00 am", "10:00 am", "Unavailable"),
        ]

        court = Court(
            name="Test Court",
            sport_type="Tennis",
            location="Test Location",
            capacity="3",
            availability_status="Fully Booked",
            date="07/11/2025",
            time_slots=time_slots,
        )

        self.assertEqual(court.time_slot, "0/2 available")

    def test_parse_court_data_no_table(self):
        """Test parsing when no frwebsearch_output_table is found."""
        html = "<html><body><div>No table here</div></body></html>"
        soup = BeautifulSoup(html, "html.parser")

        courts = self.extractor.parse_court_data(soup)
        self.assertEqual(len(courts), 0)

    def test_parse_court_data_no_tbody(self):
        """Test parsing when table exists but no tbody."""
        html = """
        <html><body>
            <table id="frwebsearch_output_table">
                <thead><tr><th>Header</th></tr></thead>
            </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        courts = self.extractor.parse_court_data(soup)
        self.assertEqual(len(courts), 0)

    def test_parse_court_data_single_court(self):
        """Test parsing a single court without time slots."""
        html = """
        <html><body>
            <table id="frwebsearch_output_table">
                <tbody>
                    <tr>
                        <td class="label-cell" data-title="Date">
                            <span class="dateblock" data-tooltip="07/11/2025">
                                <span class="dateblock__month">Jul</span>
                                <span class="dateblock__day">11</span>
                            </span>
                        </td>
                        <td class="label-cell" data-title="Facility Description">DCP Tennis Court 1</td>
                        <td class="label-cell" data-title="Location Description">Doral Central Park</td>
                        <td class="label-cell" data-title="Class Description">Tennis Court</td>
                        <td class="label-cell" data-title="Capacity">3</td>
                        <td class="label-cell" data-title="Price">$0.00/$0.00</td>
                    </tr>
                </tbody>
            </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        courts = self.extractor.parse_court_data(soup)

        self.assertEqual(len(courts), 1)
        court = courts[0]
        self.assertEqual(court.name, "DCP Tennis Court 1")
        self.assertEqual(court.sport_type, "Tennis")
        self.assertEqual(court.location, "Doral Central Park")
        self.assertEqual(court.date, "07/11/2025")
        self.assertEqual(court.price, "$0.00/$0.00")
        self.assertEqual(court.availability_status, "No Schedule")
        self.assertEqual(len(court.time_slots), 0)

    def test_parse_court_data_pickleball_court(self):
        """Test parsing a pickleball court."""
        html = """
        <html><body>
            <table id="frwebsearch_output_table">
                <tbody>
                    <tr>
                        <td class="label-cell" data-title="Date">07/11/2025</td>
                        <td class="label-cell" data-title="Facility Description">DCP Pickleball Court 1A</td>
                        <td class="label-cell" data-title="Location Description">Doral Central Park</td>
                        <td class="label-cell" data-title="Class Description">Pickleball Court</td>
                        <td class="label-cell" data-title="Capacity">4</td>
                        <td class="label-cell" data-title="Price">$5.00/$5.00</td>
                    </tr>
                </tbody>
            </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        courts = self.extractor.parse_court_data(soup)

        self.assertEqual(len(courts), 1)
        court = courts[0]
        self.assertEqual(court.name, "DCP Pickleball Court 1A")
        self.assertEqual(court.sport_type, "Pickleball")
        self.assertEqual(court.location, "Doral Central Park")

    def test_extract_time_slots_no_next_row(self):
        """Test time slot extraction when there's no next row."""
        html = """
        <tr>
            <td class="label-cell" data-title="Facility Description">Test Court</td>
        </tr>
        """
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")

        time_slots = self.extractor._extract_time_slots(row)
        self.assertEqual(len(time_slots), 0)

    def test_extract_time_slots_no_cart_blocks(self):
        """Test time slot extraction when next row has no cart-blocks."""
        html = """
        <tbody>
            <tr>
                <td class="label-cell" data-title="Facility Description">Test Court</td>
            </tr>
            <tr>
                <td class="other-cell">No cart blocks here</td>
            </tr>
        </tbody>
        """
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")

        time_slots = self.extractor._extract_time_slots(row)
        self.assertEqual(len(time_slots), 0)

    def test_extract_time_slots_unavailable(self):
        """Test extracting unavailable time slots."""
        html = """
        <tbody>
            <tr>
                <td class="label-cell" data-title="Facility Description">Test Court</td>
            </tr>
            <tr>
                <td class="cart-blocks" colspan="8">
                    <span class="cart-button cart-button--state-label">Book Now:</span>
                    <a class="button full-block error cart-button cart-button--state-block cart-button--display-multiline"
                       href="#" data-icon-primary="ui-icon-close" data-tooltip="Unavailable">
                        <span>8:00 am - 9:00 am</span>
                        <span>Unavailable</span>
                    </a>
                    <a class="button full-block error cart-button cart-button--state-block cart-button--display-multiline"
                       href="#" data-icon-primary="ui-icon-close" data-tooltip="Unavailable">
                        <span>9:00 am - 10:00 am</span>
                        <span>Unavailable</span>
                    </a>
                </td>
            </tr>
        </tbody>
        """
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")

        time_slots = self.extractor._extract_time_slots(row)

        self.assertEqual(len(time_slots), 2)

        slot1 = time_slots[0]
        self.assertEqual(slot1.start_time, "8:00 am")
        self.assertEqual(slot1.end_time, "9:00 am")
        self.assertEqual(slot1.status, "Unavailable")

        slot2 = time_slots[1]
        self.assertEqual(slot2.start_time, "9:00 am")
        self.assertEqual(slot2.end_time, "10:00 am")
        self.assertEqual(slot2.status, "Unavailable")

    def test_extract_time_slots_available(self):
        """Test extracting available time slots."""
        html = """
        <tbody>
            <tr>
                <td class="label-cell" data-title="Facility Description">Test Court</td>
            </tr>
            <tr>
                <td class="cart-blocks" colspan="8">
                    <a class="button multi-select full-block success instant-overlay cart-button cart-button--state-block"
                       href="#" data-tooltip="Book Now">8:00 am - 9:00 am</a>
                    <a class="button multi-select full-block success instant-overlay cart-button cart-button--state-block"
                       href="#" data-tooltip="Book Now">10:00 am - 11:00 am</a>
                </td>
            </tr>
        </tbody>
        """
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")

        time_slots = self.extractor._extract_time_slots(row)

        self.assertEqual(len(time_slots), 2)

        slot1 = time_slots[0]
        self.assertEqual(slot1.start_time, "8:00 am")
        self.assertEqual(slot1.end_time, "9:00 am")
        self.assertEqual(slot1.status, "Available")

        slot2 = time_slots[1]
        self.assertEqual(slot2.start_time, "10:00 am")
        self.assertEqual(slot2.end_time, "11:00 am")
        self.assertEqual(slot2.status, "Available")

    def test_extract_time_slots_mixed_availability(self):
        """Test extracting mixed available and unavailable time slots."""
        html = """
        <tbody>
            <tr>
                <td class="label-cell" data-title="Facility Description">Test Court</td>
            </tr>
            <tr>
                <td class="cart-blocks" colspan="8">
                    <a class="button multi-select full-block success instant-overlay cart-button cart-button--state-block"
                       href="#" data-tooltip="Book Now">8:00 am - 9:00 am</a>
                    <a class="button full-block error cart-button cart-button--state-block cart-button--display-multiline"
                       href="#" data-tooltip="Unavailable">
                        <span>9:00 am - 10:00 am</span>
                        <span>Unavailable</span>
                    </a>
                    <a class="button multi-select full-block success instant-overlay cart-button cart-button--state-block"
                       href="#" data-tooltip="Book Now">10:00 am - 11:00 am</a>
                </td>
            </tr>
        </tbody>
        """
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")

        time_slots = self.extractor._extract_time_slots(row)

        self.assertEqual(len(time_slots), 3)
        self.assertEqual(time_slots[0].status, "Available")
        self.assertEqual(time_slots[1].status, "Unavailable")
        self.assertEqual(time_slots[2].status, "Available")

    def test_parse_court_data_with_time_slots_available(self):
        """Test parsing court data with available time slots."""
        html = """
        <html><body>
            <table id="frwebsearch_output_table">
                <tbody>
                    <tr>
                        <td class="label-cell" data-title="Date">07/11/2025</td>
                        <td class="label-cell" data-title="Facility Description">Test Court</td>
                        <td class="label-cell" data-title="Location Description">Test Location</td>
                        <td class="label-cell" data-title="Class Description">Tennis Court</td>
                        <td class="label-cell" data-title="Capacity">3</td>
                        <td class="label-cell" data-title="Price">$10.00</td>
                    </tr>
                    <tr>
                        <td class="cart-blocks" colspan="8">
                            <a class="button multi-select full-block success instant-overlay cart-button cart-button--state-block"
                               href="#" data-tooltip="Book Now">8:00 am - 9:00 am</a>
                        </td>
                    </tr>
                </tbody>
            </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        courts = self.extractor.parse_court_data(soup)

        self.assertEqual(len(courts), 1)
        court = courts[0]
        self.assertEqual(court.availability_status, "Available")
        self.assertEqual(len(court.time_slots), 1)
        self.assertEqual(court.time_slots[0].status, "Available")

    def test_parse_court_data_with_time_slots_fully_booked(self):
        """Test parsing court data with all unavailable time slots."""
        html = """
        <html><body>
            <table id="frwebsearch_output_table">
                <tbody>
                    <tr>
                        <td class="label-cell" data-title="Date">07/11/2025</td>
                        <td class="label-cell" data-title="Facility Description">Test Court</td>
                        <td class="label-cell" data-title="Location Description">Test Location</td>
                        <td class="label-cell" data-title="Class Description">Tennis Court</td>
                        <td class="label-cell" data-title="Capacity">3</td>
                        <td class="label-cell" data-title="Price">$10.00</td>
                    </tr>
                    <tr>
                        <td class="cart-blocks" colspan="8">
                            <a class="button full-block error cart-button" href="#">
                                <span>8:00 am - 9:00 am</span>
                                <span>Unavailable</span>
                            </a>
                            <a class="button full-block error cart-button" href="#">
                                <span>9:00 am - 10:00 am</span>
                                <span>Unavailable</span>
                            </a>
                        </td>
                    </tr>
                </tbody>
            </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        courts = self.extractor.parse_court_data(soup)

        self.assertEqual(len(courts), 1)
        court = courts[0]
        self.assertEqual(court.availability_status, "Fully Booked")
        self.assertEqual(len(court.time_slots), 2)
        self.assertTrue(all(slot.status == "Unavailable" for slot in court.time_slots))

    def test_parse_court_data_insufficient_cells(self):
        """Test parsing when a row has insufficient cells."""
        html = """
        <html><body>
            <table id="frwebsearch_output_table">
                <tbody>
                    <tr>
                        <td class="label-cell" data-title="Date">07/11/2025</td>
                        <td class="label-cell" data-title="Facility Description">Test Court</td>
                        <!-- Missing required cells -->
                    </tr>
                </tbody>
            </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        courts = self.extractor.parse_court_data(soup)
        self.assertEqual(len(courts), 0)  # Should skip rows with insufficient cells

    def test_parse_court_data_multiple_courts(self):
        """Test parsing multiple courts."""
        html = """
        <html><body>
            <table id="frwebsearch_output_table">
                <tbody>
                    <tr>
                        <td class="label-cell" data-title="Date">07/11/2025</td>
                        <td class="label-cell" data-title="Facility Description">Tennis Court 1</td>
                        <td class="label-cell" data-title="Location Description">Location 1</td>
                        <td class="label-cell" data-title="Class Description">Tennis Court</td>
                        <td class="label-cell" data-title="Capacity">3</td>
                        <td class="label-cell" data-title="Price">$10.00</td>
                    </tr>
                    <tr>
                        <td class="cart-blocks" colspan="8">
                            <!-- Time slots for court 1 -->
                        </td>
                    </tr>
                    <tr>
                        <td class="label-cell" data-title="Date">07/11/2025</td>
                        <td class="label-cell" data-title="Facility Description">Pickleball Court 1</td>
                        <td class="label-cell" data-title="Location Description">Location 2</td>
                        <td class="label-cell" data-title="Class Description">Pickleball Court</td>
                        <td class="label-cell" data-title="Capacity">4</td>
                        <td class="label-cell" data-title="Price">$5.00</td>
                    </tr>
                    <tr>
                        <td class="cart-blocks" colspan="8">
                            <!-- Time slots for court 2 -->
                        </td>
                    </tr>
                </tbody>
            </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        courts = self.extractor.parse_court_data(soup)

        self.assertEqual(len(courts), 2)
        self.assertEqual(courts[0].name, "Tennis Court 1")
        self.assertEqual(courts[0].sport_type, "Tennis")
        self.assertEqual(courts[1].name, "Pickleball Court 1")
        self.assertEqual(courts[1].sport_type, "Pickleball")

    @patch("doral_courts.core.html_extractor.logger")
    def test_logging_behavior(self, mock_logger):
        """Test that appropriate logging messages are generated."""
        html = """
        <html><body>
            <table id="frwebsearch_output_table">
                <tbody>
                    <tr>
                        <td class="label-cell" data-title="Date">07/11/2025</td>
                        <td class="label-cell" data-title="Facility Description">Test Court</td>
                        <td class="label-cell" data-title="Location Description">Test Location</td>
                        <td class="label-cell" data-title="Class Description">Tennis Court</td>
                        <td class="label-cell" data-title="Capacity">3</td>
                        <td class="label-cell" data-title="Price">$10.00</td>
                    </tr>
                </tbody>
            </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        courts = self.extractor.parse_court_data(soup)

        # Verify that debug and info logging calls were made
        mock_logger.debug.assert_called()
        mock_logger.info.assert_called()

        # Check for specific log messages
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        self.assertTrue(
            any("Starting court data parsing" in call for call in debug_calls)
        )
        self.assertTrue(
            any("frwebsearch_output_tables" in call for call in debug_calls)
        )

    def test_extract_time_slots_malformed_time_range(self):
        """Test parsing time slots with malformed time range."""
        html = """
        <tbody>
            <tr>
                <td class="label-cell" data-title="Facility Description">Test Court</td>
            </tr>
            <tr>
                <td class="cart-blocks" colspan="8">
                    <a class="button multi-select full-block success instant-overlay cart-button cart-button--state-block"
                       href="#" data-tooltip="Book Now">Invalid time format</a>
                </td>
            </tr>
        </tbody>
        """
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")

        time_slots = self.extractor._extract_time_slots(row)

        self.assertEqual(len(time_slots), 1)
        slot = time_slots[0]
        self.assertEqual(slot.start_time, "Invalid time format")
        self.assertEqual(slot.end_time, "")
        self.assertEqual(slot.status, "Available")

    def test_extract_time_slots_insufficient_spans(self):
        """Test parsing time slots with insufficient span elements."""
        html = """
        <tbody>
            <tr>
                <td class="label-cell" data-title="Facility Description">Test Court</td>
            </tr>
            <tr>
                <td class="cart-blocks" colspan="8">
                    <a class="button full-block error cart-button cart-button--state-block cart-button--display-multiline"
                       href="#" data-tooltip="Unavailable">
                        <!-- Missing span with time -->
                    </a>
                </td>
            </tr>
        </tbody>
        """
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")

        time_slots = self.extractor._extract_time_slots(row)

        # Should skip buttons with insufficient spans
        self.assertEqual(len(time_slots), 0)

    def test_parse_court_data_missing_optional_fields(self):
        """Test parsing court data with missing optional fields."""
        html = """
        <html><body>
            <table id="frwebsearch_output_table">
                <tbody>
                    <tr>
                        <td class="label-cell" data-title="Date">07/11/2025</td>
                        <td class="label-cell" data-title="Facility Description">Minimal Court</td>
                        <!-- Missing location, class, capacity, price but have enough label-cells -->
                        <td class="label-cell">Other data</td>
                        <td class="label-cell">More data</td>
                        <td class="label-cell">Even more</td>
                    </tr>
                </tbody>
            </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        courts = self.extractor.parse_court_data(soup)

        self.assertEqual(len(courts), 1)
        court = courts[0]
        self.assertEqual(court.name, "Minimal Court")
        self.assertEqual(court.location, "Unknown Location")  # Default value
        self.assertEqual(
            court.sport_type, "Pickleball"
        )  # Default when no tennis indicator
        self.assertIsNone(court.price)  # Should be None when missing

    def test_sport_type_detection_from_name(self):
        """Test sport type detection from court name when class description is missing."""
        html = """
        <html><body>
            <table id="frwebsearch_output_table">
                <tbody>
                    <tr>
                        <td class="label-cell" data-title="Date">07/11/2025</td>
                        <td class="label-cell" data-title="Facility Description">Tennis Court Complex</td>
                        <td class="label-cell" data-title="Location Description">Test Location</td>
                        <td class="label-cell" data-title="Class Description"></td>
                        <td class="label-cell" data-title="Capacity">3</td>
                        <td class="label-cell" data-title="Price">$10.00</td>
                    </tr>
                </tbody>
            </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        courts = self.extractor.parse_court_data(soup)

        self.assertEqual(len(courts), 1)
        court = courts[0]
        self.assertEqual(court.sport_type, "Tennis")  # Detected from name

    def test_date_extraction_fallback(self):
        """Test date extraction fallback when dateblock is not available."""
        html = """
        <html><body>
            <table id="frwebsearch_output_table">
                <tbody>
                    <tr>
                        <td class="label-cell" data-title="Date">07/12/2025</td>
                        <td class="label-cell" data-title="Facility Description">Test Court</td>
                        <td class="label-cell" data-title="Location Description">Test Location</td>
                        <td class="label-cell" data-title="Class Description">Tennis Court</td>
                        <td class="label-cell" data-title="Capacity">3</td>
                        <td class="label-cell" data-title="Price">$10.00</td>
                    </tr>
                </tbody>
            </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        courts = self.extractor.parse_court_data(soup)

        self.assertEqual(len(courts), 1)
        court = courts[0]
        self.assertEqual(court.date, "07/12/2025")  # Should use text content

    @patch("doral_courts.core.html_extractor.logger")
    def test_error_handling_in_court_parsing(self, mock_logger):
        """Test error handling when court parsing fails."""
        # Create a malformed HTML that will cause an exception
        html = """
        <html><body>
            <table id="frwebsearch_output_table">
                <tbody>
                    <tr>
                        <td class="label-cell" data-title="Date">07/11/2025</td>
                        <td class="label-cell" data-title="Facility Description">Test Court</td>
                        <td class="label-cell" data-title="Location Description">Test Location</td>
                        <td class="label-cell" data-title="Class Description">Tennis Court</td>
                        <td class="label-cell" data-title="Capacity">3</td>
                        <td class="label-cell" data-title="Price">$10.00</td>
                    </tr>
                </tbody>
            </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        # Mock an exception in the parsing process
        with patch.object(
            self.extractor, "_extract_time_slots", side_effect=Exception("Test error")
        ):
            courts = self.extractor.parse_court_data(soup)

        # Should handle the error gracefully and continue
        self.assertEqual(len(courts), 0)  # Court should be skipped due to error
        mock_logger.warning.assert_called()


if __name__ == "__main__":
    unittest.main()
