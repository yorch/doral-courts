# Development Guide

Guide for developers who want to contribute to or extend the Doral Courts CLI.

## Architecture Overview

The application follows a modern Python package structure with clear separation of concerns:

```
src/doral_courts/
├── cli/                    # Command-line interface
│   ├── commands/          # Individual command modules
│   └── main.py           # CLI entry point and command registration
├── core/                  # Core business logic
│   ├── scraper.py        # Web scraping with Cloudflare bypass
│   ├── html_extractor.py # HTML parsing and data models
│   └── database.py       # SQLite database operations
├── display/               # UI formatting and display
│   ├── tables.py         # Rich table displays
│   ├── detailed.py       # Detailed data views
│   └── lists.py          # List-based displays
└── utils/                 # Utility functions
    ├── logger.py         # Logging configuration
    ├── date_utils.py     # Date parsing utilities
    └── file_utils.py     # File I/O operations
```

## Modular CLI Architecture

The CLI uses a modular command structure where each command is in its own module:

```
cli/commands/
├── list_cmd.py                # Main court listing command
├── stats_cmd.py               # Database statistics
├── slots_cmd.py               # Time slot details
├── data_cmd.py                # Comprehensive data view
├── cleanup_cmd.py             # Data cleanup
├── history_cmd.py             # Historical data
├── watch_cmd.py               # Real-time monitoring
├── list_available_slots_cmd.py # Available slots listing
├── list_courts_cmd.py         # Court names listing
└── list_locations_cmd.py      # Location listing
```

Each command module:

- Defines a single Click command
- Handles its own options and arguments
- Imports only required dependencies
- Follows consistent error handling patterns

## Core Components

### CLI Layer (`cli/`)

**main.py**

- CLI entry point using Click framework
- Command registration and global options
- Context management for shared state

**commands/**

- Individual command implementations
- Each command is self-contained
- Consistent parameter validation
- Rich progress indicators and error handling

### Core Logic (`core/`)

**scraper.py**

- Web scraping using cloudscraper (Cloudflare bypass)
- HTTP request handling with retry logic
- Pagination support for multi-page results
- Rate limiting and deduplication

**html_extractor.py**

- BeautifulSoup-based HTML parsing
- Data model definitions (Court, TimeSlot dataclasses)
- Court availability detection
- Time slot extraction and status parsing

**database.py**

- SQLite database operations
- Historical data storage and retrieval
- Data migration handling
- Statistics and analytics queries

### Display Layer (`display/`)

**tables.py**

- Rich table formatting for court data
- Availability status color coding
- Time slot summaries and breakdowns

**detailed.py**

- Comprehensive court data displays
- Time slot analysis and summaries
- Panel-based detailed views

**lists.py**

- Simple list displays for court names
- Location summaries with counts
- Filtered and sorted outputs

### Utilities (`utils/`)

**logger.py**

- Centralized logging configuration
- Configurable verbosity levels
- Module-specific loggers

**date_utils.py**

- Flexible date parsing (relative, absolute, offsets)
- Date validation and formatting
- Business logic for date handling

**file_utils.py**

- Data export functionality (HTML/JSON)
- File naming conventions
- Directory management

## Development Setup

### Prerequisites

- Python 3.13+
- uv (recommended) or pip
- Git

### Setup

```bash
# Clone and setup
git clone https://github.com/yorch/doral-courts.git
uv sync --group dev

# Verify setup
uv run doral-courts --help
uv run pytest -v
```

### Testing

```bash
# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/unit/test_html_extractor.py -v

# Watch mode for development
uv run pytest --watch
```

### Code Quality

```bash
# Linting with ruff
uv run ruff check src/

# Formatting with ruff
uv run ruff format src/

# Type checking with mypy
uv run mypy src/
```

## Project Structure

```
doral-courts/
├── src/
│   └── doral_courts/           # Main package
│       ├── __init__.py         # Package initialization
│       ├── cli/                # CLI commands and interface
│       ├── core/               # Business logic
│       ├── display/            # UI formatting
│       └── utils/              # Utility functions
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test data
├── docs/                       # Documentation
├── data/                       # Exported data files
├── pyproject.toml              # Project configuration
└── README.md                   # Project overview
```

## Adding New Commands

To add a new command:

1. **Create command module** in `src/doral_courts/cli/commands/`:

```python
# src/doral_courts/cli/commands/my_cmd.py
import click
from rich.console import Console
from ...core.database import Database
from ...utils.logger import get_logger

logger = get_logger(__name__)
console = Console()

@click.command()
@click.option('--option', help='Command option')
@click.pass_context
def my_command(ctx, option):
    """Description of my command."""
    logger.info("Running my command")
    # Implementation here
```

2. **Register command** in `src/doral_courts/cli/main.py`:

```python
from .commands.my_cmd import my_command

# Add to CLI group
cli.add_command(my_command)
```

3. **Add tests** in `tests/unit/`:

```python
# tests/unit/test_my_cmd.py
import pytest
from click.testing import CliRunner
from doral_courts.cli.commands.my_cmd import my_command

def test_my_command():
    runner = CliRunner()
    result = runner.invoke(my_command, ['--option', 'value'])
    assert result.exit_code == 0
```

## Best Practices

### Code Organization

- **Single Responsibility**: Each module has a clear, single purpose
- **Dependency Injection**: Pass dependencies rather than importing globally
- **Error Handling**: Consistent error handling patterns across commands
- **Logging**: Use module-specific loggers with appropriate levels

### CLI Design

- **Progressive Disclosure**: Simple commands by default, options for complexity
- **Consistent Naming**: Follow established patterns for options and commands
- **Rich Output**: Use colors and formatting for better UX
- **Context Awareness**: Use Click context for shared state

### Testing

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test command workflows end-to-end
- **Fixtures**: Use realistic test data
- **Mocking**: Mock external dependencies (web requests, file I/O)

### Documentation

- **Docstrings**: Comprehensive docstrings for all public functions
- **Type Hints**: Use type hints for better code clarity
- **Examples**: Include usage examples in documentation
- **Architecture**: Keep architecture documentation updated

## Debugging

### Development Tools

```bash
# Run with verbose logging
uv run doral-courts --verbose list

# Save data for analysis
uv run doral-courts --save-data list

# Interactive debugging
uv run python -c "
from doral_courts.core.scraper import Scraper
scraper = Scraper()
# Interactive debugging here
"
```

### Common Issues

1. **Import Errors**: Ensure you're using relative imports within the package
2. **CLI Not Found**: Make sure `uv sync` was run to install the CLI entry point
3. **Test Failures**: Run `uv run pytest -v` to see detailed test output
4. **Web Scraping**: Use `--save-data` to inspect raw HTML for parsing issues

## Performance Considerations

- **Caching**: Database caching for historical data
- **Pagination**: Efficient handling of multi-page results
- **Deduplication**: Prevent duplicate data in database
- **Rate Limiting**: Respectful web scraping practices

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make changes and add tests
4. Run the test suite: `uv run pytest`
5. Run code quality checks: `uv run ruff check src/`
6. Commit with descriptive messages
7. Push to your fork and create a pull request

For more details, see [CONTRIBUTING.md](../CONTRIBUTING.md).
