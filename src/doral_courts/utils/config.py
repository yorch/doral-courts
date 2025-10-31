"""Configuration management for Doral Courts CLI."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .logger import get_logger

logger = get_logger(__name__)


def get_config_dir() -> Path:
    """
    Get the configuration directory path for Doral Courts.

    Returns:
        Path to the config directory (~/.doral-courts)

    The directory is created if it doesn't exist.
    """
    config_dir = Path.home() / ".doral-courts"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


class Config:
    """
    Manage user configuration for Doral Courts CLI.

    Handles YAML configuration file at ~/.doral-courts/config.yaml with support for:
    - Favorite courts
    - Saved queries
    - Default preferences (sport, date offset)

    Features:
        - Automatic config directory creation
        - Default configuration generation
        - Safe YAML reading/writing
        - Validation of configuration structure

    Usage:
        config = Config()
        favorites = config.get_favorites()
        config.add_favorite("DLP Tennis Court 1")
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Optional custom config path (default: ~/.doral-courts/config.yaml)
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_dir = get_config_dir()
            self.config_path = self.config_dir / "config.yaml"

        logger.debug(f"Config path: {self.config_path}")
        self._ensure_config_exists()

    def _ensure_config_exists(self) -> None:
        """Create config file with defaults if it doesn't exist."""
        # Create default config file if needed
        if not self.config_path.exists():
            logger.info(f"Creating default config file: {self.config_path}")
            default_config = {
                "favorites": {"courts": []},
                "queries": {},
                "defaults": {
                    "sport": None,
                    "date_offset": 0,  # 0 = today, 1 = tomorrow
                },
            }
            self._write_config(default_config)

    def _read_config(self) -> Dict[str, Any]:
        """
        Read configuration from YAML file.

        Returns:
            Configuration dictionary

        Raises:
            yaml.YAMLError: If config file is malformed
        """
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f) or {}
                logger.debug(f"Loaded config: {config}")
                return config
        except yaml.YAMLError as e:
            logger.error(f"Error reading config file: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error reading config: {e}")
            return {}

    def _write_config(self, config: Dict[str, Any]) -> None:
        """
        Write configuration to YAML file.

        Args:
            config: Configuration dictionary to write

        Raises:
            yaml.YAMLError: If config cannot be serialized
        """
        try:
            with open(self.config_path, "w") as f:
                yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
                logger.debug(f"Wrote config: {config}")
        except Exception as e:
            logger.error(f"Error writing config file: {e}")
            raise

    def get_favorites(self) -> List[str]:
        """
        Get list of favorite court names.

        Returns:
            List of court names
        """
        config = self._read_config()
        return config.get("favorites", {}).get("courts", [])

    def add_favorite(self, court_name: str) -> bool:
        """
        Add a court to favorites.

        Args:
            court_name: Name of court to add

        Returns:
            True if added, False if already exists
        """
        config = self._read_config()
        favorites = config.get("favorites", {}).get("courts", [])

        if court_name in favorites:
            logger.warning(f"Court '{court_name}' already in favorites")
            return False

        favorites.append(court_name)
        if "favorites" not in config:
            config["favorites"] = {}
        config["favorites"]["courts"] = favorites

        self._write_config(config)
        logger.info(f"Added '{court_name}' to favorites")
        return True

    def remove_favorite(self, court_name: str) -> bool:
        """
        Remove a court from favorites.

        Args:
            court_name: Name of court to remove

        Returns:
            True if removed, False if not found
        """
        config = self._read_config()
        favorites = config.get("favorites", {}).get("courts", [])

        if court_name not in favorites:
            logger.warning(f"Court '{court_name}' not in favorites")
            return False

        favorites.remove(court_name)
        config["favorites"]["courts"] = favorites

        self._write_config(config)
        logger.info(f"Removed '{court_name}' from favorites")
        return True

    def get_queries(self) -> Dict[str, Dict[str, str]]:
        """
        Get all saved queries.

        Returns:
            Dictionary of query name -> query parameters
        """
        config = self._read_config()
        return config.get("queries", {})

    def get_query(self, query_name: str) -> Optional[Dict[str, str]]:
        """
        Get a specific saved query.

        Args:
            query_name: Name of the query

        Returns:
            Query parameters or None if not found
        """
        queries = self.get_queries()
        return queries.get(query_name)

    def add_query(self, query_name: str, parameters: Dict[str, str]) -> None:
        """
        Add or update a saved query.

        Args:
            query_name: Name for the query
            parameters: Query parameters (sport, date, status, location, etc.)
        """
        config = self._read_config()
        if "queries" not in config:
            config["queries"] = {}

        config["queries"][query_name] = parameters
        self._write_config(config)
        logger.info(f"Saved query '{query_name}' with parameters: {parameters}")

    def remove_query(self, query_name: str) -> bool:
        """
        Remove a saved query.

        Args:
            query_name: Name of query to remove

        Returns:
            True if removed, False if not found
        """
        config = self._read_config()
        queries = config.get("queries", {})

        if query_name not in queries:
            logger.warning(f"Query '{query_name}' not found")
            return False

        del config["queries"][query_name]
        self._write_config(config)
        logger.info(f"Removed query '{query_name}'")
        return True

    def get_default(self, key: str) -> Optional[Any]:
        """
        Get a default configuration value.

        Args:
            key: Configuration key (e.g., 'sport', 'date_offset')

        Returns:
            Configuration value or None
        """
        config = self._read_config()
        return config.get("defaults", {}).get(key)

    def set_default(self, key: str, value: Any) -> None:
        """
        Set a default configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        config = self._read_config()
        if "defaults" not in config:
            config["defaults"] = {}

        config["defaults"][key] = value
        self._write_config(config)
        logger.info(f"Set default '{key}' to '{value}'")
