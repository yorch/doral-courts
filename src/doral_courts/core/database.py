import sqlite3
from datetime import datetime
from typing import List, Optional

from ..utils.logger import get_logger
from .html_extractor import Court, TimeSlot

logger = get_logger(__name__)


class Database:
    """
    SQLite database interface for storing and retrieving court availability data.

    Provides methods for storing court information, time slots, and querying
    historical data. Handles database schema creation, migrations, and data
    cleanup operations.

    Database Schema:
        courts: Main court information with availability status
        time_slots: Individual time slot details linked to courts

    Features:
        - Automatic schema migration support
        - Duplicate prevention with unique constraints
        - Historical data tracking with timestamps
        - Efficient querying with proper indexing

    Usage:
        db = Database()
        db.insert_courts(courts_list)
        historical_courts = db.get_courts(sport_type="Tennis")
    """

    def __init__(self, db_path: str = "doral_courts.db"):
        """
        Initialize database connection and setup schema.

        Args:
            db_path: Path to SQLite database file (default: "doral_courts.db")

        Creates database file if it doesn't exist and sets up required tables
        and indexes. Performs any necessary schema migrations.
        """
        self.db_path = db_path
        logger.debug("Initializing database at path: %s", db_path)
        self.init_database()

    def init_database(self):
        """
        Initialize the database with required tables and indexes.

        Creates the court and time_slots tables with proper schema and
        constraints. Handles schema migrations (e.g., surface_type -> capacity
        column rename). Sets up indexes for efficient querying.

        Tables Created:
            courts: Main court data with unique constraint on (name, date, time_slot)
            time_slots: Individual time slots with foreign key to courts

        Indexes Created:
            - idx_sport_type: For filtering by sport
            - idx_availability: For filtering by availability status
            - idx_date: For date-based queries
            - idx_time_slots_*: For time slot queries

        Migration Support:
            - Renames legacy surface_type column to capacity
            - Maintains backward compatibility
        """
        logger.debug("Setting up database schema")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS courts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    sport_type TEXT NOT NULL,
                    location TEXT NOT NULL,
                    capacity TEXT NOT NULL,
                    availability_status TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time_slot TEXT NOT NULL,
                    price TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, date, time_slot)
                )
            """
            )

            # Migration: Check if surface_type column exists and rename it to capacity
            cursor.execute("PRAGMA table_info(courts)")
            columns = [column[1] for column in cursor.fetchall()]
            if "surface_type" in columns and "capacity" not in columns:
                logger.info("Migrating database: renaming surface_type to capacity")
                cursor.execute(
                    "ALTER TABLE courts RENAME COLUMN surface_type TO capacity"
                )
            logger.debug("Created courts table")

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS time_slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    court_id INTEGER NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    status TEXT NOT NULL,
                    date TEXT NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (court_id) REFERENCES courts (id) ON DELETE CASCADE,
                    UNIQUE(court_id, start_time, end_time, date)
                )
            """
            )
            logger.debug("Created time_slots table")

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sport_type
                ON courts(sport_type)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_availability
                ON courts(availability_status)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_date
                ON courts(date)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_time_slots_court_id
                ON time_slots(court_id)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_time_slots_date
                ON time_slots(date)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_time_slots_status
                ON time_slots(status)
            """
            )
            logger.debug("Created database indexes")

            conn.commit()

        logger.info("Database initialized successfully")

    def insert_courts(self, courts: List[Court]) -> int:
        """
        Insert or update court data in the database.

        Stores court information and associated time slots. Uses INSERT OR REPLACE
        to handle duplicate entries based on unique constraint (name, date, time_slot).
        Each court's time slots are stored in the separate time_slots table.

        Args:
            courts: List of Court objects to insert/update

        Returns:
            Number of courts successfully inserted or updated

        Database Operations:
            1. Insert/update main court record in courts table
            2. Clear existing time slots for the court and date
            3. Insert new time slots in time_slots table
            4. All operations are transactional (commit at end)

        Error Handling:
            - Logs errors for individual courts but continues processing
            - Uses database transactions for consistency
            - Returns count of successful insertions

        Example:
            db = Database()
            count = db.insert_courts(scraped_courts)
            print(f"Inserted {count} courts")
        """
        logger.info("Inserting %d courts into database", len(courts))
        inserted_count = 0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for i, court in enumerate(courts):
                try:
                    logger.debug(
                        "Inserting court %d/%d: %s", i + 1, len(courts), court.name
                    )

                    # Insert or update the main court record
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO courts
                        (name, sport_type, location, capacity, availability_status,
                         date, time_slot, price, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                        (
                            court.name,
                            court.sport_type,
                            court.location,
                            court.capacity,
                            court.availability_status,
                            court.date,
                            court.time_slot,
                            court.price,
                        ),
                    )

                    # Get the court ID
                    court_id = cursor.lastrowid
                    if court_id is None:
                        # If INSERT OR REPLACE updated an existing record, get the ID
                        cursor.execute(
                            """
                            SELECT id FROM courts
                            WHERE name = ? AND date = ? AND time_slot = ?
                        """,
                            (court.name, court.date, court.time_slot),
                        )
                        result = cursor.fetchone()
                        court_id = result[0] if result else None

                    # Insert time slots if available
                    if court_id and court.time_slots:
                        logger.debug(
                            "Inserting %d time slots for court %s",
                            len(court.time_slots),
                            court.name,
                        )

                        # Clear existing time slots for this court and date
                        cursor.execute(
                            """
                            DELETE FROM time_slots
                            WHERE court_id = ? AND date = ?
                        """,
                            (court_id, court.date),
                        )

                        # Insert new time slots
                        for slot in court.time_slots:
                            cursor.execute(
                                """
                                INSERT INTO time_slots
                                (court_id, start_time, end_time, status, date, last_updated)
                                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                            """,
                                (
                                    court_id,
                                    slot.start_time,
                                    slot.end_time,
                                    slot.status,
                                    court.date,
                                ),
                            )

                    inserted_count += 1

                except sqlite3.Error as e:
                    logger.error("Error inserting court %s: %s", court.name, e)

            conn.commit()

        logger.info("Successfully inserted/updated %d courts", inserted_count)
        return inserted_count

    def get_courts(
        self,
        sport_type: Optional[str] = None,
        availability_status: Optional[str] = None,
        date: Optional[str] = None,
    ) -> List[Court]:
        """Retrieve courts from the database with optional filters."""
        logger.debug(
            "Querying courts with filters - Sport: %s, Status: %s, Date: %s",
            sport_type,
            availability_status,
            date,
        )

        query = "SELECT id, name, sport_type, location, capacity, availability_status, date, time_slot, price FROM courts WHERE 1=1"
        params = []

        if sport_type:
            query += " AND sport_type = ?"
            params.append(sport_type)

        if availability_status:
            query += " AND availability_status = ?"
            params.append(availability_status)

        if date:
            query += " AND date = ?"
            params.append(date)

        query += " ORDER BY date, time_slot, sport_type, name"

        logger.debug("Executing query: %s with params: %s", query, params)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        logger.debug("Query returned %d rows", len(rows))

        courts = []
        for i, row in enumerate(rows):
            court_id = row[0]

            # Load time slots for this court
            time_slots = self._load_time_slots(court_id, row[6])  # row[6] is the date

            court = Court(
                name=row[1],
                sport_type=row[2],
                location=row[3],
                capacity=row[4],
                availability_status=row[5],
                date=row[6],
                time_slots=time_slots,
                price=row[8],
            )
            courts.append(court)
            logger.debug(
                "Loaded court %d: %s with %d time slots",
                i + 1,
                court.name,
                len(time_slots),
            )

        logger.info("Retrieved %d courts from database", len(courts))
        return courts

    def _load_time_slots(self, court_id: int, date: str) -> List[TimeSlot]:
        """Load time slots for a specific court and date."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT start_time, end_time, status
                FROM time_slots
                WHERE court_id = ? AND date = ?
                ORDER BY start_time
            """,
                (court_id, date),
            )
            rows = cursor.fetchall()

        time_slots = []
        for row in rows:
            time_slot = TimeSlot(start_time=row[0], end_time=row[1], status=row[2])
            time_slots.append(time_slot)

        return time_slots

    def clear_old_data(self, days_old: int = 7):
        """Remove court data older than specified days."""
        logger.info("Clearing data older than %d days", days_old)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # First count how many will be deleted
            cursor.execute(
                """
                SELECT COUNT(*) FROM courts
                WHERE last_updated < datetime('now', '-' || ? || ' days')
            """,
                (days_old,),
            )
            count_to_delete = cursor.fetchone()[0]
            logger.debug("Found %d court records to delete", count_to_delete)

            # Count time slots to be deleted
            cursor.execute(
                """
                SELECT COUNT(*) FROM time_slots
                WHERE last_updated < datetime('now', '-' || ? || ' days')
            """,
                (days_old,),
            )
            time_slots_to_delete = cursor.fetchone()[0]
            logger.debug("Found %d time slot records to delete", time_slots_to_delete)

            # Delete time slots first (due to foreign key constraints)
            cursor.execute(
                """
                DELETE FROM time_slots
                WHERE last_updated < datetime('now', '-' || ? || ' days')
            """,
                (days_old,),
            )

            # Delete courts
            cursor.execute(
                """
                DELETE FROM courts
                WHERE last_updated < datetime('now', '-' || ? || ' days')
            """,
                (days_old,),
            )

            conn.commit()

        logger.info(
            "Deleted %d court records and %d time slot records",
            count_to_delete,
            time_slots_to_delete,
        )

    def get_stats(self) -> dict:
        """Get database statistics."""
        logger.debug("Generating database statistics")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM courts")
            total_courts = cursor.fetchone()[0]
            logger.debug("Total courts in database: %d", total_courts)

            cursor.execute(
                "SELECT sport_type, COUNT(*) FROM courts GROUP BY sport_type"
            )
            sport_counts = dict(cursor.fetchall())
            logger.debug("Sport breakdown: %s", sport_counts)

            cursor.execute(
                "SELECT availability_status, COUNT(*) FROM courts GROUP BY availability_status"
            )
            availability_counts = dict(cursor.fetchall())
            logger.debug("Availability breakdown: %s", availability_counts)

            cursor.execute("SELECT MAX(last_updated) FROM courts")
            last_update = cursor.fetchone()[0]
            logger.debug("Last update: %s", last_update)

        stats = {
            "total_courts": total_courts,
            "sport_counts": sport_counts,
            "availability_counts": availability_counts,
            "last_updated": last_update,
        }

        logger.info("Generated database statistics")
        return stats
