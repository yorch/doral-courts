"""Tests for the Database layer (SQLite backend)."""

from doral_courts.core.html_extractor import Court, TimeSlot


class TestInsertAndDedup:
    def test_insert_single_court(self, db, make_court):
        count = db.insert_courts([make_court()])
        assert count == 1
        courts = db.get_courts()
        assert len(courts) == 1
        assert courts[0].name == "DCP Tennis Court 1"

    def test_reinsert_same_key_updates_not_duplicates(self, db, make_court):
        db.insert_courts([make_court(availability_status="Available")])
        # Same (name, date), changed availability and slots -> must update.
        db.insert_courts(
            [
                make_court(
                    availability_status="Fully Booked",
                    time_slots=[TimeSlot("8:00 am", "9:00 am", "Unavailable")],
                )
            ]
        )
        courts = db.get_courts()
        assert len(courts) == 1
        assert courts[0].availability_status == "Fully Booked"

    def test_update_does_not_orphan_time_slots(self, db, make_court):
        db.insert_courts(
            [
                make_court(
                    time_slots=[
                        TimeSlot("8:00 am", "9:00 am", "Available"),
                        TimeSlot("9:00 am", "10:00 am", "Available"),
                    ]
                )
            ]
        )
        db.insert_courts(
            [make_court(time_slots=[TimeSlot("8:00 am", "9:00 am", "Unavailable")])]
        )

        # Exactly the latest slot should remain; no orphaned rows.
        conn = db.adapter.connect()
        cursor = db.adapter.execute(conn, "SELECT COUNT(*) FROM time_slots")
        total = db.adapter.fetchone(cursor)[0]
        conn.close()
        assert total == 1

        courts = db.get_courts()
        assert len(courts[0].time_slots) == 1
        assert courts[0].time_slots[0].status == "Unavailable"

    def test_distinct_dates_are_separate_rows(self, db, make_court):
        db.insert_courts([make_court(date="07/12/2025")])
        db.insert_courts([make_court(date="07/13/2025")])
        assert len(db.get_courts()) == 2


class TestGetCourts:
    def test_filter_by_sport(self, db, make_court):
        db.insert_courts(
            [
                make_court(name="Tennis 1", sport_type="Tennis"),
                make_court(name="Pickle 1", sport_type="Pickleball"),
            ]
        )
        tennis = db.get_courts(sport_type="Tennis")
        assert [c.name for c in tennis] == ["Tennis 1"]

    def test_filter_by_date(self, db, make_court):
        db.insert_courts(
            [
                make_court(name="A", date="07/12/2025"),
                make_court(name="B", date="07/13/2025"),
            ]
        )
        only = db.get_courts(date="07/13/2025")
        assert [c.name for c in only] == ["B"]

    def test_results_sorted_chronologically(self, db, make_court):
        db.insert_courts([make_court(name="Later", date="01/01/2027")])
        db.insert_courts([make_court(name="Earlier", date="12/31/2024")])
        courts = db.get_courts()
        assert [c.name for c in courts] == ["Earlier", "Later"]

    def test_time_slots_sorted_chronologically(self, db, make_court):
        db.insert_courts(
            [
                make_court(
                    time_slots=[
                        TimeSlot("10:00 am", "11:00 am", "Available"),
                        TimeSlot("8:00 am", "9:00 am", "Available"),
                    ]
                )
            ]
        )
        slots = db.get_courts()[0].time_slots
        assert [s.start_time for s in slots] == ["8:00 am", "10:00 am"]


class TestStatsAndCleanup:
    def test_get_stats(self, db, make_court):
        db.insert_courts(
            [
                make_court(name="T1", sport_type="Tennis"),
                make_court(name="P1", sport_type="Pickleball"),
            ]
        )
        stats = db.get_stats()
        assert stats["total_courts"] == 2
        assert stats["sport_counts"].get("Tennis") == 1
        assert stats["sport_counts"].get("Pickleball") == 1

    def test_clear_old_data_keeps_recent(self, db, make_court):
        db.insert_courts([make_court()])
        # Nothing is older than 7 days yet, so cleanup should keep it.
        db.clear_old_data(days_old=7)
        assert len(db.get_courts()) == 1


class TestIsoDateStorage:
    def test_dates_stored_as_iso(self, db, make_court):
        db.insert_courts([make_court(date="07/12/2025")])
        conn = db.adapter.connect()
        court_date = db.adapter.fetch_scalar(
            db.adapter.execute(conn, "SELECT date FROM courts")
        )
        slot_date = db.adapter.fetch_scalar(
            db.adapter.execute(conn, "SELECT date FROM time_slots")
        )
        conn.close()
        assert court_date == "2025-07-12"
        assert slot_date == "2025-07-12"

    def test_court_date_round_trips_to_mmddyyyy(self, db, make_court):
        db.insert_courts([make_court(date="07/12/2025")])
        assert db.get_courts()[0].date == "07/12/2025"

    def test_date_filter_accepts_mmddyyyy(self, db, make_court):
        db.insert_courts([make_court(name="A", date="07/12/2025")])
        db.insert_courts([make_court(name="B", date="07/13/2025")])
        result = db.get_courts(date="07/13/2025")
        assert [c.name for c in result] == ["B"]

    def test_ordering_across_year_boundary(self, db, make_court):
        # The bug this fixes: MM/DD/YYYY text sorts 01/02/2026 before 12/31/2025.
        db.insert_courts([make_court(name="Jan", date="01/02/2026")])
        db.insert_courts([make_court(name="Dec", date="12/31/2025")])
        assert [c.date for c in db.get_courts()] == ["12/31/2025", "01/02/2026"]


class TestDateMigration:
    def test_legacy_mmddyyyy_dates_converted_in_place(self, tmp_path):
        """Existing MM/DD/YYYY rows are rewritten to ISO on open, preserving
        the data (not dropped)."""
        import sqlite3

        from doral_courts.core.database import Database
        from doral_courts.core.db_adapter import SQLiteAdapter

        path = str(tmp_path / "legacy_dates.db")
        conn = sqlite3.connect(path)
        conn.executescript(
            """
            CREATE TABLE courts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
                sport_type TEXT NOT NULL, location TEXT NOT NULL,
                capacity TEXT NOT NULL, availability_status TEXT NOT NULL,
                date TEXT NOT NULL, time_slot TEXT NOT NULL, price TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, date)
            );
            CREATE TABLE time_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT, court_id INTEGER NOT NULL,
                start_time TEXT NOT NULL, end_time TEXT NOT NULL,
                status TEXT NOT NULL, date TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO courts
                (name, sport_type, location, capacity, availability_status,
                 date, time_slot, price)
                VALUES ('Court 1', 'Tennis', 'DCP', '4', 'Available',
                        '07/12/2025', '1/1 available', '$10');
            INSERT INTO time_slots (court_id, start_time, end_time, status, date)
                VALUES (1, '8:00 am', '9:00 am', 'Available', '07/12/2025');
            """
        )
        conn.commit()
        conn.close()

        db = Database(adapter=SQLiteAdapter(db_path=path))
        conn = db.adapter.connect()
        court_date = db.adapter.fetch_scalar(
            db.adapter.execute(conn, "SELECT date FROM courts")
        )
        slot_date = db.adapter.fetch_scalar(
            db.adapter.execute(conn, "SELECT date FROM time_slots")
        )
        count = db.adapter.fetch_scalar(
            db.adapter.execute(conn, "SELECT COUNT(*) FROM courts")
        )
        conn.close()
        assert court_date == "2025-07-12"
        assert slot_date == "2025-07-12"
        assert count == 1  # data preserved, not dropped


class TestLegacyMigration:
    def test_legacy_unique_constraint_is_rebuilt(self, tmp_path):
        """A DB created with the legacy UNIQUE(name, date, time_slot) key
        must be rebuilt so re-inserts dedupe on (name, date)."""
        import sqlite3

        from doral_courts.core.database import Database
        from doral_courts.core.db_adapter import SQLiteAdapter

        path = str(tmp_path / "legacy.db")
        conn = sqlite3.connect(path)
        conn.execute(
            """
            CREATE TABLE courts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, sport_type TEXT NOT NULL,
                location TEXT NOT NULL, capacity TEXT NOT NULL,
                availability_status TEXT NOT NULL, date TEXT NOT NULL,
                time_slot TEXT NOT NULL, price TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, date, time_slot)
            )
            """
        )
        conn.commit()
        conn.close()

        # Opening via Database() should detect and rebuild the legacy schema.
        db = Database(adapter=SQLiteAdapter(db_path=path))
        court = Court(
            "Court 1",
            "Tennis",
            "DCP",
            "4",
            "Available",
            "07/12/2025",
            [TimeSlot("8:00 am", "9:00 am", "Available")],
            "$10",
        )
        db.insert_courts([court])
        db.insert_courts(
            [
                Court(
                    "Court 1",
                    "Tennis",
                    "DCP",
                    "4",
                    "Fully Booked",
                    "07/12/2025",
                    [TimeSlot("8:00 am", "9:00 am", "Unavailable")],
                    "$10",
                )
            ]
        )
        # Correct dedup => single row, not two.
        assert len(db.get_courts()) == 1
