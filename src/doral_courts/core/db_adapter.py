"""Database adapter for supporting multiple database backends."""

import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List, Optional, Tuple, cast

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Backend-neutral aliases. Concrete adapters return sqlite3 or psycopg2
# objects, so the abstract contract must not pin itself to one driver.
Connection = Any
Cursor = Any
Row = Tuple[Any, ...]


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters.

    Subclasses expose a ``dialect`` attribute (``"sqlite"`` or
    ``"postgresql"``) so callers can branch on backend behaviour without
    sniffing for driver-specific attributes.
    """

    #: Short identifier for the backend, e.g. ``"sqlite"`` / ``"postgresql"``.
    dialect: str

    @abstractmethod
    def connect(self) -> Connection:
        """Create and return a database connection."""
        pass

    @abstractmethod
    def execute(
        self,
        conn: Connection,
        query: str,
        params: Optional[Tuple] = None,
    ) -> Cursor:
        """Execute a query and return cursor."""
        pass

    @abstractmethod
    def executemany(
        self,
        conn: Connection,
        query: str,
        params_list: List[Tuple],
    ) -> Cursor:
        """Execute a query multiple times with different parameters."""
        pass

    @abstractmethod
    def fetchall(self, cursor: Cursor) -> List[Row]:
        """Fetch all results from cursor."""
        pass

    @abstractmethod
    def fetchone(self, cursor: Cursor) -> Optional[Row]:
        """Fetch one result from cursor."""
        pass

    @abstractmethod
    def commit(self, conn: Connection) -> None:
        """Commit transaction."""
        pass

    @abstractmethod
    def close(self, conn: Connection) -> None:
        """Close connection."""
        pass

    @abstractmethod
    def get_placeholder(self) -> str:
        """Get parameter placeholder for this database.

        Returns '?' for SQLite, '%s' for PostgreSQL.
        """
        pass

    def fetch_scalar(self, cursor: Cursor, default: object = None) -> object:
        """Fetch the first column of the first row, or ``default`` if no row.

        Convenience for single-value queries (``COUNT(*)``, ``MAX(...)``, an id
        lookup) so callers don't repeat the None-guard.
        """
        row = self.fetchone(cursor)
        if row is None:
            return default
        value: object = row[0]
        return value

    @abstractmethod
    def id_column_sql(self) -> str:
        """Return the DDL fragment for an auto-incrementing primary key."""
        pass

    @abstractmethod
    def older_than_clause(self, placeholder: str) -> str:
        """Return a WHERE fragment matching rows older than N days.

        The fragment references the ``last_updated`` column and expects a
        single bound parameter (the number of days) supplied via
        ``placeholder``.
        """
        pass


class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter."""

    dialect = "sqlite"

    def __init__(self, db_path: str | Path = "doral_courts.db") -> None:
        """
        Initialize SQLite adapter.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        logger.debug("SQLite adapter initialized with path: %s", db_path)

    def connect(self) -> Connection:
        """Create SQLite connection with foreign key enforcement enabled."""
        conn = sqlite3.connect(self.db_path)
        # SQLite disables foreign keys per-connection by default, which makes
        # ON DELETE CASCADE inert. Enable it on every connection.
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def execute(
        self,
        conn: Connection,
        query: str,
        params: Optional[Tuple] = None,
    ) -> Cursor:
        """Execute query on SQLite connection."""
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

    def executemany(
        self,
        conn: Connection,
        query: str,
        params_list: List[Tuple],
    ) -> Cursor:
        """Execute query multiple times on SQLite connection."""
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        return cursor

    def fetchall(self, cursor: Cursor) -> List[Row]:
        """Fetch all results from SQLite cursor."""
        rows: List[Row] = cursor.fetchall()
        return rows

    def fetchone(self, cursor: Cursor) -> Optional[Row]:
        """Fetch one result from SQLite cursor."""
        row: Optional[Row] = cursor.fetchone()
        return row

    def commit(self, conn: Connection) -> None:
        """Commit SQLite transaction."""
        conn.commit()

    def close(self, conn: Connection) -> None:
        """Close SQLite connection."""
        conn.close()

    def get_placeholder(self) -> str:
        """Get SQLite parameter placeholder."""
        return "?"

    def id_column_sql(self) -> str:
        """Return SQLite auto-increment primary key DDL."""
        return "id INTEGER PRIMARY KEY AUTOINCREMENT"

    def older_than_clause(self, placeholder: str) -> str:
        """Return SQLite 'older than N days' predicate."""
        return f"last_updated < datetime('now', '-' || {placeholder} || ' days')"


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter."""

    dialect = "postgresql"

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "doral_courts",
        user: str = "postgres",
        password: str = "",
    ) -> None:
        """
        Initialize PostgreSQL adapter.

        Args:
            host: PostgreSQL server host
            port: PostgreSQL server port
            database: Database name
            user: Database user
            password: Database password
        """
        try:
            import psycopg2

            self.psycopg2 = psycopg2
        except ImportError as err:
            raise ImportError(
                "psycopg2-binary is required for PostgreSQL"
                " support. Install it with: "
                "uv pip install doral-courts[postgresql]"
            ) from err

        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

        logger.debug(
            "PostgreSQL adapter initialized: %s@%s:%s/%s",
            user,
            host,
            port,
            database,
        )

    def connect(self) -> Connection:
        """Create PostgreSQL connection."""
        return self.psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
        )

    def execute(
        self,
        conn: Connection,
        query: str,
        params: Optional[Tuple] = None,
    ) -> Cursor:
        """Execute query on PostgreSQL connection."""
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

    def executemany(
        self,
        conn: Connection,
        query: str,
        params_list: List[Tuple],
    ) -> Cursor:
        """Execute query multiple times on PostgreSQL connection."""
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        return cursor

    def fetchall(self, cursor: Cursor) -> List[Row]:
        """Fetch all results from PostgreSQL cursor."""
        rows: List[Row] = cursor.fetchall()
        return rows

    def fetchone(self, cursor: Cursor) -> Optional[Row]:
        """Fetch one result from PostgreSQL cursor."""
        row: Optional[Row] = cursor.fetchone()
        return row

    def commit(self, conn: Connection) -> None:
        """Commit PostgreSQL transaction."""
        conn.commit()

    def close(self, conn: Connection) -> None:
        """Close PostgreSQL connection."""
        conn.close()

    def get_placeholder(self) -> str:
        """Get PostgreSQL parameter placeholder."""
        return "%s"

    def id_column_sql(self) -> str:
        """Return PostgreSQL auto-increment primary key DDL."""
        return "id SERIAL PRIMARY KEY"

    def older_than_clause(self, placeholder: str) -> str:
        """Return PostgreSQL 'older than N days' predicate."""
        return f"last_updated < NOW() - ({placeholder} || ' days')::interval"


def create_adapter(
    db_config: dict[str, object],
) -> DatabaseAdapter:
    """
    Create appropriate database adapter based on configuration.

    Args:
        db_config: Database configuration dictionary

    Returns:
        DatabaseAdapter instance (SQLite or PostgreSQL)

    Raises:
        ValueError: If database type is not supported
    """
    db_type = str(db_config.get("type", "sqlite")).lower()

    if db_type == "sqlite":
        sqlite_config = cast(dict, db_config.get("sqlite", {}))
        db_path = sqlite_config.get("path", "doral_courts.db")
        logger.info("Creating SQLite adapter with path: %s", db_path)
        return SQLiteAdapter(db_path=db_path)

    elif db_type == "postgresql":
        pg_config = cast(dict, db_config.get("postgresql", {}))
        logger.info(
            "Creating PostgreSQL adapter for %s@%s:%s/%s",
            pg_config.get("user"),
            pg_config.get("host"),
            pg_config.get("port"),
            pg_config.get("database"),
        )
        return PostgreSQLAdapter(
            host=pg_config.get("host", "localhost"),
            port=pg_config.get("port", 5432),
            database=pg_config.get("database", "doral_courts"),
            user=pg_config.get("user", "postgres"),
            password=pg_config.get("password", ""),
        )

    else:
        raise ValueError(
            f"Unsupported database type: {db_type}. Supported types: sqlite, postgresql"
        )
