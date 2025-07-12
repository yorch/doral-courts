import logging
import sys
from typing import Optional

def setup_logging(verbose: bool = False, log_file: Optional[str] = None):
    """
    Configure logging for the application.

    Sets up console and optional file logging with appropriate levels and
    formatting. Suppresses verbose logging from external libraries when
    not in debug mode to reduce noise.

    Args:
        verbose: Enable DEBUG level logging if True, INFO level if False
        log_file: Optional path to log file for persistent logging

    Logging Configuration:
        - Console output to stderr with timestamp and module info
        - DEBUG level when verbose=True, INFO level otherwise
        - Optional file logging always at DEBUG level
        - External library noise suppression in non-verbose mode

    Format:
        "YYYY-MM-DD HH:MM:SS - module.name - LEVEL - message"

    External Libraries Suppressed:
        - requests: Set to WARNING level when not verbose
        - urllib3: Set to WARNING level when not verbose

    Example:
        setup_logging(verbose=True, log_file="doral-courts.log")
    """

    # Set log level based on verbose flag
    log_level = logging.DEBUG if verbose else logging.INFO

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Suppress verbose logging from external libraries unless in debug mode
    if not verbose:
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Creates and returns a logger instance configured with the module name.
    Should be called at module level to create a logger for that specific
    module, enabling fine-grained logging control.

    Args:
        name: Module name, typically __name__ when called from module level

    Returns:
        logging.Logger: Configured logger instance for the module

    Usage:
        # At module level
        logger = get_logger(__name__)

        # In functions
        logger.info("Processing started")
        logger.debug("Detailed debugging info")
        logger.error("Something went wrong")

    Note:
        Logger behavior depends on global configuration set by setup_logging().
        Call setup_logging() before using any loggers.
    """
    return logging.getLogger(name)
