from typing import List, Optional

from ..utils.config import Config
from ..utils.date_utils import from_iso_date, time_sort_key, to_iso_date
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

    def __init__(
        self,
        db_path: Optional[str] = None,
        adapter: Optional[DatabaseAdapter] = None,
    ) -> None:
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
            self.db_path = getattr(adapter, "db_path", None)
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
            self.db_path = getattr(self.adapter, "db_path", None)
            logger.debug(
                "Database adapter created from config: %s", db_config.get("type")
            )

        self.init_database()

    def init_database(self) -> None:
        """
        Initialize the database with required tables and indexes.

        Creates the court and time_slots tables with proper schema and
        constraints. Handles schema migrations (e.g., surface_type -> capacity
        column rename). Sets up indexes for efficient querying.

        Tables Created:
            courts: Main court data with unique constraint on (name, date)
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
            id_column = self.adapter.id_column_sql()

            # Migration: older versions used UNIQUE(name, date, time_slot),
            # where time_slot held a computed availability summary. That broke
            # deduplication (changed availability => new row). Rebuild the
            # cache if the legacy constraint is detected (SQLite only).
            self._migrate_legacy_unique_constraint(conn)

            # Create courts table
            cursor = self.adapter.execute(
                conn,
                f"""
                CREATE TABLE IF NOT EXISTS courts (
                    {id_column},"""  # noqa: S608
                """
                    name TEXT NOT NULL,
                    sport_type TEXT NOT NULL,
                    location TEXT NOT NULL,
                    capacity TEXT NOT NULL,
                    availability_status TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time_slot TEXT NOT NULL,
                    price TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, date)
                )
            """,
            )
            logger.debug("Created courts table")

            # Migration: Check if surface_type column exists and rename it to capacity
            # This is SQLite-specific, skip for PostgreSQL
            if self.adapter.dialect == "sqlite":
                cursor = self.adapter.execute(conn, "PRAGMA table_info(courts)")
                columns = [column[1] for column in self.adapter.fetchall(cursor)]
                if "surface_type" in columns and "capacity" not in columns:
                    logger.info("Migrating database: renaming surface_type to capacity")
                    self.adapter.execute(
                        conn,
                        "ALTER TABLE courts RENAME COLUMN surface_type TO capacity",
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
            """,
            )
            logger.debug("Created time_slots table")

            # Create indexes
            self.adapter.execute(
                conn,
                """
                CREATE INDEX IF NOT EXISTS idx_sport_type
                ON courts(sport_type)
            """,
            )

            self.adapter.execute(
                conn,
                """
                CREATE INDEX IF NOT EXISTS idx_availability
                ON courts(availability_status)
            """,
            )

            self.adapter.execute(
                conn,
                """
                CREATE INDEX IF NOT EXISTS idx_date
                ON courts(date)
            """,
            )

            self.adapter.execute(
                conn,
                """
                CREATE INDEX IF NOT EXISTS idx_time_slots_court_id
                ON time_slots(court_id)
            """,
            )

            self.adapter.execute(
                conn,
                """
                CREATE INDEX IF NOT EXISTS idx_time_slots_date
                ON time_slots(date)
            """,
            )

            self.adapter.execute(
                conn,
                """
                CREATE INDEX IF NOT EXISTS idx_time_slots_status
                ON time_slots(status)
            """,
            )
            logger.debug("Created database indexes")

            # Convert any legacy MM/DD/YYYY dates left by older versions to ISO.
            self._migrate_date_format_to_iso(conn)

            self.adapter.commit(conn)
            logger.info("Database initialized successfully")
        finally:
            self.adapter.close(conn)

    def _migrate_date_format_to_iso(self, conn: object) -> None:
        """Convert any stored ``MM/DD/YYYY`` dates to ISO ``YYYY-MM-DD``.

        Older versions stored dates in ``MM/DD/YYYY`` form, which sorts and
        range-compares incorrectly as text. This rewrites existing rows in
        place (preserving historical tracking data) and is idempotent: once
        converted, no value contains ``/`` so it becomes a no-op. Works on both
        backends and runs after the tables exist.
        """
        placeholder = self.adapter.get_placeholder()
        for table in ("courts", "time_slots"):
            cursor = self.adapter.execute(
                conn,
                f"SELECT DISTINCT date FROM {table} WHERE date LIKE '%/%'",  # noqa: S608
            )
            legacy_dates = [r[0] for r in self.adapter.fetchall(cursor)]
            for old in legacy_dates:
                iso = to_iso_date(old)
                if iso != old:
                    self.adapter.execute(
                        conn,
                        f"UPDATE {table} SET date = {placeholder} "  # noqa: S608
                        f"WHERE date = {placeholder}",
                        (iso, old),
                    )
            if legacy_dates:
                logger.info(
                    "Migrated %d legacy date value(s) to ISO in %s",
                    len(legacy_dates),
                    table,
                )

    def _migrate_legacy_unique_constraint(self, conn: object) -> None:
        """Drop the cached courts table if it uses the legacy unique key.

        Old schemas declared ``UNIQUE(name, date, time_slot)``. Because
        ``time_slot`` is a derived availability summary, that key produced a
        new row every time availability changed, defeating deduplication.
        The courts data is a re-fetchable local cache, so the safe upgrade is
        to drop the legacy tables and let them be recreated with the correct
        ``UNIQUE(name, date)`` key. SQLite only; PostgreSQL deployments are
        new and never had the legacy schema.
        """
        if self.adapter.dialect != "sqlite":
            return

        cursor = self.adapter.execute(
            conn,
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='courts'",
        )
        row = self.adapter.fetchone(cursor)
        if not row or not row[0]:
            return

        normalized = "".join(row[0].split()).lower()
        if "unique(name,date,time_slot)" in normalized:
            logger.warning(
                "Detected legacy database schema (UNIQUE on time_slot); "
                "rebuilding court cache with corrected unique key"
            )
            self.adapter.execute(conn, "DROP TABLE IF EXISTS time_slots")
            self.adapter.execute(conn, "DROP TABLE IF EXISTS courts")
            self.adapter.commit(conn)

    def insert_courts(self, courts: List[Court]) -> int:
        """
        Insert or update court data in the database.

        Stores court information and associated time slots. Uses
        INSERT ... ON CONFLICT(name, date) DO UPDATE to handle duplicate entries,
        preserving the existing row id so child time slots are not orphaned.
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
        failed_count = 0

        conn = self.adapter.connect()
        try:
            placeholder = self.adapter.get_placeholder()

            # Build the per-court statements once; they don't vary per iteration.
            # ON CONFLICT ... DO UPDATE is supported by both SQLite (>= 3.24) and
            # PostgreSQL and, unlike INSERT OR REPLACE, preserves the existing row
            # id so child time_slots are not orphaned. Conflict target is the
            # natural key (name, date).
            upsert_sql = f"""
                INSERT INTO courts
                (name, sport_type, location, capacity, availability_status,
                 date, time_slot, price, last_updated)
                VALUES (
                    {placeholder}, {placeholder}, {placeholder}, {placeholder},
                    {placeholder}, {placeholder}, {placeholder}, {placeholder},
                    CURRENT_TIMESTAMP
                )
                ON CONFLICT (name, date)
                DO UPDATE SET
                    sport_type = EXCLUDED.sport_type,
                    location = EXCLUDED.location,
                    capacity = EXCLUDED.capacity,
                    availability_status = EXCLUDED.availability_status,
                    time_slot = EXCLUDED.time_slot,
                    price = EXCLUDED.price,
                    last_updated = CURRENT_TIMESTAMP
            """  # noqa: S608
            select_id_sql = (
                f"SELECT id FROM courts WHERE name = {placeholder} "  # noqa: S608
                f"AND date = {placeholder}"
            )
            delete_slots_sql = (
                f"DELETE FROM time_slots WHERE court_id = {placeholder} "  # noqa: S608
                f"AND date = {placeholder}"
            )
            insert_slot_sql = f"""
                INSERT INTO time_slots
                (court_id, start_time, end_time, status, date, last_updated)
                VALUES (
                    {placeholder}, {placeholder}, {placeholder},
                    {placeholder}, {placeholder}, CURRENT_TIMESTAMP
                )
            """  # noqa: S608

            for i, court in enumerate(courts):
                try:
                    logger.debug(
                        "Inserting court %d/%d: %s", i + 1, len(courts), court.name
                    )

                    # Store dates as ISO (YYYY-MM-DD) so SQL ordering and range
                    # queries are correct; Court.date stays MM/DD/YYYY.
                    iso_date = to_iso_date(court.date)

                    # Insert or update the main court record.
                    self.adapter.execute(
                        conn,
                        upsert_sql,
                        (
                            court.name,
                            court.sport_type,
                            court.location,
                            court.capacity,
                            court.availability_status,
                            iso_date,
                            court.time_slot,
                            court.price,
                        ),
                    )

                    # Resolve the court id by its natural key. lastrowid is
                    # unreliable across the upsert/backends, so always look up.
                    cursor = self.adapter.execute(
                        conn, select_id_sql, (court.name, iso_date)
                    )
                    court_id = self.adapter.fetch_scalar(cursor)

                    # Replace this court's time slots for the date in one batch.
                    if court_id and court.time_slots:
                        logger.debug(
                            "Inserting %d time slots for court %s",
                            len(court.time_slots),
                            court.name,
                        )
                        self.adapter.execute(
                            conn, delete_slots_sql, (court_id, iso_date)
                        )
                        self.adapter.executemany(
                            conn,
                            insert_slot_sql,
                            [
                                (
                                    court_id,
                                    slot.start_time,
                                    slot.end_time,
                                    slot.status,
                                    iso_date,
                                )
                                for slot in court.time_slots
                            ],
                        )

                    inserted_count += 1

                except Exception as e:
                    failed_count += 1
                    logger.error("Error inserting court %s: %s", court.name, e)

            self.adapter.commit(conn)
            logger.info("Successfully inserted/updated %d courts", inserted_count)
            if failed_count:
                logger.warning(
                    "%d of %d courts failed to insert", failed_count, len(courts)
                )
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
        query = (  # noqa: S608
            "SELECT id, name, sport_type, location,"
            " capacity, availability_status,"
            " date, time_slot, price"
            " FROM courts WHERE 1=1"
        )
        params: list[str] = []

        if sport_type:
            query += f" AND sport_type = {placeholder}"  # noqa: S608
            params.append(sport_type)

        if availability_status:
            query += (  # noqa: S608
                f" AND availability_status = {placeholder}"
            )
            params.append(availability_status)

        if date:
            query += f" AND date = {placeholder}"  # noqa: S608
            params.append(to_iso_date(date))

        # Dates are stored as ISO (YYYY-MM-DD), which sorts chronologically as
        # text, so ordering can be done correctly in SQL.
        query += " ORDER BY date, sport_type, name"

        logger.debug("Executing query: %s with params: %s", query, params)

        conn = self.adapter.connect()
        try:
            cursor = self.adapter.execute(conn, query, tuple(params))
            rows = self.adapter.fetchall(cursor)

            logger.debug("Query returned %d rows", len(rows))

            # Batch-load every court's time slots in one query on this
            # connection, avoiding an N+1 connection-per-court pattern.
            court_ids = [row[0] for row in rows]
            slots_by_court = self._load_time_slots_bulk(conn, court_ids)

            courts = []
            for row in rows:
                court_id = row[0]
                time_slots = slots_by_court.get(court_id, [])

                court = Court(
                    name=row[1],
                    sport_type=row[2],
                    location=row[3],
                    capacity=row[4],
                    availability_status=row[5],
                    # Convert stored ISO date back to the app's MM/DD/YYYY form.
                    date=from_iso_date(row[6]),
                    time_slots=time_slots,
                    price=row[8],
                )
                courts.append(court)

            logger.info("Retrieved %d courts from database", len(courts))
        finally:
            self.adapter.close(conn)

        return courts

    def _load_time_slots_bulk(
        self, conn: object, court_ids: List[int]
    ) -> dict[int, List[TimeSlot]]:
        """Load time slots for many courts in a single query.

        Returns a mapping of court_id -> chronologically sorted time slots,
        reusing the provided connection.
        """
        if not court_ids:
            return {}

        placeholder = self.adapter.get_placeholder()
        placeholders = ", ".join(placeholder for _ in court_ids)
        cursor = self.adapter.execute(
            conn,
            f"""
            SELECT court_id, start_time, end_time, status
            FROM time_slots
            WHERE court_id IN ({placeholders})
        """,  # noqa: S608
            tuple(court_ids),
        )
        rows = self.adapter.fetchall(cursor)

        slots_by_court: dict[int, List[TimeSlot]] = {}
        for court_id, start_time, end_time, status in rows:
            slots_by_court.setdefault(court_id, []).append(
                TimeSlot(start_time=start_time, end_time=end_time, status=status)
            )

        # start_time is 12-hour text ("8:00 am"); sort numerically.
        for slots in slots_by_court.values():
            slots.sort(key=lambda s: time_sort_key(s.start_time))

        return slots_by_court

    def clear_old_data(self, days_old: int = 7) -> None:
        """Remove court data older than specified days."""
        logger.info("Clearing data older than %d days", days_old)

        placeholder = self.adapter.get_placeholder()
        # Backend-specific "older than N days" predicate (SQLite's datetime()
        # function does not exist in PostgreSQL).
        older_than = self.adapter.older_than_clause(placeholder)
        conn = self.adapter.connect()
        try:
            # First count how many will be deleted
            cursor = self.adapter.execute(
                conn,
                f"SELECT COUNT(*) FROM courts WHERE {older_than}",  # noqa: S608
                (days_old,),
            )
            count_to_delete = self.adapter.fetch_scalar(cursor, 0)
            logger.debug("Found %s court records to delete", count_to_delete)

            # Count time slots to be deleted
            cursor = self.adapter.execute(
                conn,
                f"SELECT COUNT(*) FROM time_slots WHERE {older_than}",  # noqa: S608
                (days_old,),
            )
            time_slots_to_delete = self.adapter.fetch_scalar(cursor, 0)
            logger.debug(
                "Found %s time slot records to delete",
                time_slots_to_delete,
            )

            # Delete time slots first (due to foreign key constraints)
            self.adapter.execute(
                conn,
                f"DELETE FROM time_slots WHERE {older_than}",  # noqa: S608
                (days_old,),
            )

            # Delete courts
            self.adapter.execute(
                conn,
                f"DELETE FROM courts WHERE {older_than}",  # noqa: S608
                (days_old,),
            )

            self.adapter.commit(conn)

            logger.info(
                "Deleted %s court records and %s time slot records",
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
            total_courts = self.adapter.fetch_scalar(cursor, 0)
            logger.debug("Total courts in database: %s", total_courts)

            cursor = self.adapter.execute(
                conn, "SELECT sport_type, COUNT(*) FROM courts GROUP BY sport_type"
            )
            sport_counts: dict = dict(self.adapter.fetchall(cursor))
            logger.debug("Sport breakdown: %s", sport_counts)

            cursor = self.adapter.execute(
                conn,
                "SELECT availability_status, COUNT(*)"
                " FROM courts"
                " GROUP BY availability_status",
            )
            availability_counts: dict = dict(self.adapter.fetchall(cursor))
            logger.debug("Availability breakdown: %s", availability_counts)

            cursor = self.adapter.execute(conn, "SELECT MAX(last_updated) FROM courts")
            last_update = self.adapter.fetch_scalar(cursor)
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
