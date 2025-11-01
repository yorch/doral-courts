"""Database adapter for supporting multiple database backends."""

import sqlite3
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple

from ..utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters."""

    @abstractmethod
    def connect(self) -> Any:
        """Create and return a database connection."""
        pass

    @abstractmethod
    def execute(
        self, conn: Any, query: str, params: Optional[Tuple] = None
    ) -> Any:
        """Execute a query and return cursor."""
        pass

    @abstractmethod
    def executemany(
        self, conn: Any, query: str, params_list: List[Tuple]
    ) -> Any:
        """Execute a query multiple times with different parameters."""
        pass

    @abstractmethod
    def fetchall(self, cursor: Any) -> List[Tuple]:
        """Fetch all results from cursor."""
        pass

    @abstractmethod
    def fetchone(self, cursor: Any) -> Optional[Tuple]:
        """Fetch one result from cursor."""
        pass

    @abstractmethod
    def commit(self, conn: Any) -> None:
        """Commit transaction."""
        pass

    @abstractmethod
    def close(self, conn: Any) -> None:
        """Close connection."""
        pass

    @abstractmethod
    def get_placeholder(self) -> str:
        """Get parameter placeholder for this database ('?' for SQLite, '%s' for PostgreSQL)."""
        pass


class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter."""

    def __init__(self, db_path: str = "doral_courts.db"):
        """
        Initialize SQLite adapter.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        logger.debug(f"SQLite adapter initialized with path: {db_path}")

    def connect(self) -> sqlite3.Connection:
        """Create SQLite connection."""
        return sqlite3.connect(self.db_path)

    def execute(
        self, conn: sqlite3.Connection, query: str, params: Optional[Tuple] = None
    ) -> sqlite3.Cursor:
        """Execute query on SQLite connection."""
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

    def executemany(
        self, conn: sqlite3.Connection, query: str, params_list: List[Tuple]
    ) -> sqlite3.Cursor:
        """Execute query multiple times on SQLite connection."""
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        return cursor

    def fetchall(self, cursor: sqlite3.Cursor) -> List[Tuple]:
        """Fetch all results from SQLite cursor."""
        return cursor.fetchall()

    def fetchone(self, cursor: sqlite3.Cursor) -> Optional[Tuple]:
        """Fetch one result from SQLite cursor."""
        return cursor.fetchone()

    def commit(self, conn: sqlite3.Connection) -> None:
        """Commit SQLite transaction."""
        conn.commit()

    def close(self, conn: sqlite3.Connection) -> None:
        """Close SQLite connection."""
        conn.close()

    def get_placeholder(self) -> str:
        """Get SQLite parameter placeholder."""
        return "?"


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "doral_courts",
        user: str = "postgres",
        password: str = "",
    ):
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
        except ImportError:
            raise ImportError(
                "psycopg2-binary is required for PostgreSQL support. "
                "Install it with: uv pip install doral-courts[postgresql]"
            )

        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

        logger.debug(
            f"PostgreSQL adapter initialized: {user}@{host}:{port}/{database}"
        )

    def connect(self) -> Any:
        """Create PostgreSQL connection."""
        return self.psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
        )

    def execute(
        self, conn: Any, query: str, params: Optional[Tuple] = None
    ) -> Any:
        """Execute query on PostgreSQL connection."""
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

    def executemany(
        self, conn: Any, query: str, params_list: List[Tuple]
    ) -> Any:
        """Execute query multiple times on PostgreSQL connection."""
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        return cursor

    def fetchall(self, cursor: Any) -> List[Tuple]:
        """Fetch all results from PostgreSQL cursor."""
        return cursor.fetchall()

    def fetchone(self, cursor: Any) -> Optional[Tuple]:
        """Fetch one result from PostgreSQL cursor."""
        return cursor.fetchone()

    def commit(self, conn: Any) -> None:
        """Commit PostgreSQL transaction."""
        conn.commit()

    def close(self, conn: Any) -> None:
        """Close PostgreSQL connection."""
        conn.close()

    def get_placeholder(self) -> str:
        """Get PostgreSQL parameter placeholder."""
        return "%s"


def create_adapter(db_config: dict) -> DatabaseAdapter:
    """
    Create appropriate database adapter based on configuration.

    Args:
        db_config: Database configuration dictionary from config.yaml

    Returns:
        DatabaseAdapter instance (SQLite or PostgreSQL)

    Raises:
        ValueError: If database type is not supported
    """
    db_type = db_config.get("type", "sqlite").lower()

    if db_type == "sqlite":
        sqlite_config = db_config.get("sqlite", {})
        db_path = sqlite_config.get("path", "doral_courts.db")
        logger.info(f"Creating SQLite adapter with path: {db_path}")
        return SQLiteAdapter(db_path=db_path)

    elif db_type == "postgresql":
        pg_config = db_config.get("postgresql", {})
        logger.info(
            f"Creating PostgreSQL adapter for {pg_config.get('user')}@"
            f"{pg_config.get('host')}:{pg_config.get('port')}/{pg_config.get('database')}"
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
