from datetime import datetime
from typing import List, Optional

from ..utils.config import Config
from ..utils.logger import get_logger
from .db_adapter import DatabaseAdapter, create_adapter
from .html_extractor import Court, TimeSlot

logger = get_logger(__name__)


class Database:
    """
    Database interface for storing and retrieving court availability data.

    Supports both SQLite and PostgreSQL backends through configuration.

    Provides methods for storing court information, time slots, and querying
    historical data. Handles database schema creation, migrations, and data
    cleanup operations.

    Database Schema:
        courts: Main court information with availability status
        time_slots: Individual time slot details linked to courts

    Features:
        - Multiple database backend support (SQLite, PostgreSQL)
        - Automatic schema migration support
        - Duplicate prevention with unique constraints
        - Historical data tracking with timestamps
        - Efficient querying with proper indexing

    Usage:
        db = Database()  # Uses config from ~/.doral-courts/config.yaml
        db.insert_courts(courts_list)
        historical_courts = db.get_courts(sport_type="Tennis")
    """

    def __init__(self, db_path: Optional[str] = None, adapter: Optional[DatabaseAdapter] = None):
        """
        Initialize database connection and setup schema.

        Args:
            db_path: Optional path to SQLite database file (for backward compatibility)
            adapter: Optional database adapter (for testing or custom setups)

        Creates database if it doesn't exist and sets up required tables
        and indexes. Performs any necessary schema migrations.
        """
        if adapter:
            # Use provided adapter (for testing)
            self.adapter = adapter
            self.db_path = getattr(adapter, 'db_path', None)
            logger.debug("Using provided database adapter")
        elif db_path:
            # Legacy mode: SQLite with specific path
            from .db_adapter import SQLiteAdapter
            self.adapter = SQLiteAdapter(db_path=db_path)
            self.db_path = db_path
            logger.debug("Using SQLite adapter with path: %s", db_path)
        else:
            # Use configuration
            config = Config()
            db_config = config.get_database_config()
            self.adapter = create_adapter(db_config)
            self.db_path = getattr(self.adapter, 'db_path', None)
            logger.debug("Database adapter created from config: %s", db_config.get('type'))

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

        conn = self.adapter.connect()
        try:
            # Determine database-specific syntax
            placeholder = self.adapter.get_placeholder()

            # Use different primary key syntax for SQLite vs PostgreSQL
            if hasattr(self.adapter, 'db_path'):  # SQLite
                id_column = "id INTEGER PRIMARY KEY AUTOINCREMENT"
            else:  # PostgreSQL
                id_column = "id SERIAL PRIMARY KEY"

            # Create courts table
            cursor = self.adapter.execute(
                conn,
                f"""
                CREATE TABLE IF NOT EXISTS courts (
                    {id_column},
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
            logger.debug("Created courts table")

            # Migration: Check if surface_type column exists and rename it to capacity
            # This is SQLite-specific, skip for PostgreSQL
            if hasattr(self.adapter, 'db_path'):  # SQLite only
                cursor = self.adapter.execute(conn, "PRAGMA table_info(courts)")
                columns = [column[1] for column in self.adapter.fetchall(cursor)]
                if "surface_type" in columns and "capacity" not in columns:
                    logger.info("Migrating database: renaming surface_type to capacity")
                    self.adapter.execute(
                        conn,
                        "ALTER TABLE courts RENAME COLUMN surface_type TO capacity"
                    )

            # Create time_slots table
            cursor = self.adapter.execute(
                conn,
                f"""
                CREATE TABLE IF NOT EXISTS time_slots (
                    {id_column},
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

            # Create indexes
            self.adapter.execute(
                conn,
                """
                CREATE INDEX IF NOT EXISTS idx_sport_type
                ON courts(sport_type)
            """
            )

            self.adapter.execute(
                conn,
                """
                CREATE INDEX IF NOT EXISTS idx_availability
                ON courts(availability_status)
            """
            )

            self.adapter.execute(
                conn,
                """
                CREATE INDEX IF NOT EXISTS idx_date
                ON courts(date)
            """
            )

            self.adapter.execute(
                conn,
                """
                CREATE INDEX IF NOT EXISTS idx_time_slots_court_id
                ON time_slots(court_id)
            """
            )

            self.adapter.execute(
                conn,
                """
                CREATE INDEX IF NOT EXISTS idx_time_slots_date
                ON time_slots(date)
            """
            )

            self.adapter.execute(
                conn,
                """
                CREATE INDEX IF NOT EXISTS idx_time_slots_status
                ON time_slots(status)
            """
            )
            logger.debug("Created database indexes")

            self.adapter.commit(conn)
            logger.info("Database initialized successfully")
        finally:
            self.adapter.close(conn)

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

        conn = self.adapter.connect()
        try:
            placeholder = self.adapter.get_placeholder()

            for i, court in enumerate(courts):
                try:
                    logger.debug(
                        "Inserting court %d/%d: %s", i + 1, len(courts), court.name
                    )

                    # Insert or update the main court record
                    # Note: INSERT OR REPLACE is SQLite-specific
                    # For PostgreSQL, we'll use INSERT ... ON CONFLICT
                    if hasattr(self.adapter, 'db_path'):  # SQLite
                        cursor = self.adapter.execute(
                            conn,
                            f"""
                            INSERT OR REPLACE INTO courts
                            (name, sport_type, location, capacity, availability_status,
                             date, time_slot, price, last_updated)
                            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, CURRENT_TIMESTAMP)
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
                    else:  # PostgreSQL
                        cursor = self.adapter.execute(
                            conn,
                            f"""
                            INSERT INTO courts
                            (name, sport_type, location, capacity, availability_status,
                             date, time_slot, price, last_updated)
                            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, CURRENT_TIMESTAMP)
                            ON CONFLICT (name, date, time_slot)
                            DO UPDATE SET
                                sport_type = EXCLUDED.sport_type,
                                location = EXCLUDED.location,
                                capacity = EXCLUDED.capacity,
                                availability_status = EXCLUDED.availability_status,
                                price = EXCLUDED.price,
                                last_updated = CURRENT_TIMESTAMP
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
                    if court_id is None or court_id == 0:
                        # If INSERT OR REPLACE/ON CONFLICT updated an existing record, get the ID
                        cursor = self.adapter.execute(
                            conn,
                            f"""
                            SELECT id FROM courts
                            WHERE name = {placeholder} AND date = {placeholder} AND time_slot = {placeholder}
                        """,
                            (court.name, court.date, court.time_slot),
                        )
                        result = self.adapter.fetchone(cursor)
                        court_id = result[0] if result else None

                    # Insert time slots if available
                    if court_id and court.time_slots:
                        logger.debug(
                            "Inserting %d time slots for court %s",
                            len(court.time_slots),
                            court.name,
                        )

                        # Clear existing time slots for this court and date
                        self.adapter.execute(
                            conn,
                            f"""
                            DELETE FROM time_slots
                            WHERE court_id = {placeholder} AND date = {placeholder}
                        """,
                            (court_id, court.date),
                        )

                        # Insert new time slots
                        for slot in court.time_slots:
                            self.adapter.execute(
                                conn,
                                f"""
                                INSERT INTO time_slots
                                (court_id, start_time, end_time, status, date, last_updated)
                                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, CURRENT_TIMESTAMP)
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

                except Exception as e:
                    logger.error("Error inserting court %s: %s", court.name, e)

            self.adapter.commit(conn)
            logger.info("Successfully inserted/updated %d courts", inserted_count)
        finally:
            self.adapter.close(conn)

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

        placeholder = self.adapter.get_placeholder()
        query = "SELECT id, name, sport_type, location, capacity, availability_status, date, time_slot, price FROM courts WHERE 1=1"
        params = []

        if sport_type:
            query += f" AND sport_type = {placeholder}"
            params.append(sport_type)

        if availability_status:
            query += f" AND availability_status = {placeholder}"
            params.append(availability_status)

        if date:
            query += f" AND date = {placeholder}"
            params.append(date)

        query += " ORDER BY date, time_slot, sport_type, name"

        logger.debug("Executing query: %s with params: %s", query, params)

        conn = self.adapter.connect()
        try:
            cursor = self.adapter.execute(conn, query, tuple(params))
            rows = self.adapter.fetchall(cursor)

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
        finally:
            self.adapter.close(conn)

        return courts

    def _load_time_slots(self, court_id: int, date: str) -> List[TimeSlot]:
        """Load time slots for a specific court and date."""
        placeholder = self.adapter.get_placeholder()

        conn = self.adapter.connect()
        try:
            cursor = self.adapter.execute(
                conn,
                f"""
                SELECT start_time, end_time, status
                FROM time_slots
                WHERE court_id = {placeholder} AND date = {placeholder}
                ORDER BY start_time
            """,
                (court_id, date),
            )
            rows = self.adapter.fetchall(cursor)

            time_slots = []
            for row in rows:
                time_slot = TimeSlot(start_time=row[0], end_time=row[1], status=row[2])
                time_slots.append(time_slot)

            return time_slots
        finally:
            self.adapter.close(conn)

    def clear_old_data(self, days_old: int = 7):
        """Remove court data older than specified days."""
        logger.info("Clearing data older than %d days", days_old)

        placeholder = self.adapter.get_placeholder()
        conn = self.adapter.connect()
        try:
            # First count how many will be deleted
            cursor = self.adapter.execute(
                conn,
                f"""
                SELECT COUNT(*) FROM courts
                WHERE last_updated < datetime('now', '-' || {placeholder} || ' days')
            """,
                (days_old,),
            )
            count_to_delete = self.adapter.fetchone(cursor)[0]
            logger.debug("Found %d court records to delete", count_to_delete)

            # Count time slots to be deleted
            cursor = self.adapter.execute(
                conn,
                f"""
                SELECT COUNT(*) FROM time_slots
                WHERE last_updated < datetime('now', '-' || {placeholder} || ' days')
            """,
                (days_old,),
            )
            time_slots_to_delete = self.adapter.fetchone(cursor)[0]
            logger.debug("Found %d time slot records to delete", time_slots_to_delete)

            # Delete time slots first (due to foreign key constraints)
            self.adapter.execute(
                conn,
                f"""
                DELETE FROM time_slots
                WHERE last_updated < datetime('now', '-' || {placeholder} || ' days')
            """,
                (days_old,),
            )

            # Delete courts
            self.adapter.execute(
                conn,
                f"""
                DELETE FROM courts
                WHERE last_updated < datetime('now', '-' || {placeholder} || ' days')
            """,
                (days_old,),
            )

            self.adapter.commit(conn)

            logger.info(
                "Deleted %d court records and %d time slot records",
                count_to_delete,
                time_slots_to_delete,
            )
        finally:
            self.adapter.close(conn)

    def get_stats(self) -> dict:
        """Get database statistics."""
        logger.debug("Generating database statistics")

        conn = self.adapter.connect()
        try:
            cursor = self.adapter.execute(conn, "SELECT COUNT(*) FROM courts")
            total_courts = self.adapter.fetchone(cursor)[0]
            logger.debug("Total courts in database: %d", total_courts)

            cursor = self.adapter.execute(
                conn,
                "SELECT sport_type, COUNT(*) FROM courts GROUP BY sport_type"
            )
            sport_counts = dict(self.adapter.fetchall(cursor))
            logger.debug("Sport breakdown: %s", sport_counts)

            cursor = self.adapter.execute(
                conn,
                "SELECT availability_status, COUNT(*) FROM courts GROUP BY availability_status"
            )
            availability_counts = dict(self.adapter.fetchall(cursor))
            logger.debug("Availability breakdown: %s", availability_counts)

            cursor = self.adapter.execute(conn, "SELECT MAX(last_updated) FROM courts")
            last_update = self.adapter.fetchone(cursor)[0]
            logger.debug("Last update: %s", last_update)

            stats = {
                "total_courts": total_courts,
                "sport_counts": sport_counts,
                "availability_counts": availability_counts,
                "last_updated": last_update,
            }

            logger.info("Generated database statistics")
            return stats
        finally:
            self.adapter.close(conn)
