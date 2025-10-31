# Project Guidelines

This file provides guidance to AI Agents when working with code in this repository.

## Project Overview

This is a Python CLI application that scrapes tennis and pickleball court availability data from the Doral reservation system. It provides real-time court data, filtering options, historical tracking, and data export capabilities.

## Development Commands

### Environment Setup

```bash
# Install dependencies and create virtual environment
uv sync

# Install with development dependencies
uv sync --group dev
```

### Running the Application

```bash
# Main CLI entry point
uv run doral-courts --help

# Common commands
uv run doral-courts list                    # List all courts
uv run doral-courts list --sport tennis     # Filter by sport
uv run doral-courts stats                   # Database statistics
uv run doral-courts slots --court "Court 1" # Time slot details
uv run doral-courts data --mode summary     # Comprehensive data view
```

### Testing

```bash
# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/unit/test_html_extractor.py -v

# Run single test
uv run pytest tests/unit/test_html_extractor.py::TestCourtAvailabilityHTMLExtractor::test_court_creation_with_time_slots -v
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

## Architecture

### Package Structure

```
src/doral_courts/
├── cli/                    # Command-line interface
│   ├── commands/          # Individual command modules (10 commands)
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

### Key Design Patterns

**Modular CLI Commands**: Each CLI command is implemented in its own module under `cli/commands/`. Commands are registered in `cli/main.py`. This allows for easy addition of new commands and better separation of concerns.

**Data Flow**: The typical flow is:

1. CLI command parses user input and options
2. Scraper fetches fresh data from the Doral website using cloudscraper
3. HTML extractor parses the response into Court/TimeSlot objects
4. Database stores data for historical tracking
5. Display modules format and present data to user

**Rich CLI Output**: All user-facing output uses the Rich library for colored tables, progress bars, and formatted panels.

**Global Context**: Click context (`ctx.obj`) carries global options like `verbose` and `save_data` between commands.

## Core Data Models

### Court Object

```python
@dataclass
class Court:
    name: str                 # "DCP Tennis Court 1"
    sport_type: str          # "Tennis" or "Pickleball"
    location: str            # "Doral Central Park"
    capacity: str            # "3", "4"
    availability_status: str # "Available", "Fully Booked"
    date: str               # "MM/DD/YYYY"
    time_slots: List[TimeSlot]
    price: str = None       # "$10.00"
```

### TimeSlot Object

```python
@dataclass
class TimeSlot:
    start_time: str  # "8:00 am"
    end_time: str    # "9:00 am"
    status: str      # "Available" or "Unavailable"
```

## Web Scraping Architecture

The scraper handles complex challenges:

- **Cloudflare Protection**: Uses cloudscraper library to bypass anti-bot measures
- **Pagination**: Automatically handles multi-page results with duplicate detection
- **CSRF Tokens**: Extracts and uses CSRF tokens for authenticated requests
- **Error Handling**: Graceful degradation when website is unavailable

## Database Integration

- **SQLite**: Local database (`doral_courts.db`) for historical data tracking
- **Automatic Storage**: All fetched data is automatically stored for historical analysis
- **Deduplication**: Prevents duplicate entries while allowing updates

## Command Categories

1. **Data Fetching Commands**: `list`, `slots`, `data` - Always fetch fresh data
2. **List Commands**: `list-courts`, `list-locations`, `list-available-slots` - Specialized views
3. **Historical Commands**: `history`, `stats` - Use cached database data
4. **Utility Commands**: `cleanup`, `watch` - Data management and monitoring

## Development Guidelines

### Adding New Commands

1. Create new command file in `src/doral_courts/cli/commands/`
2. Follow the established pattern with Click decorators and Rich output
3. Import and register the command in `src/doral_courts/cli/main.py`
4. Add tests in `tests/unit/`

### Date Handling

The application supports flexible date formats:

- Relative: `today`, `tomorrow`, `yesterday`
- Offset: `+3`, `-7` (days from today)
- Absolute: `MM/DD/YYYY`, `YYYY-MM-DD`

Use `parse_date_input()` from `utils.date_utils` for consistent parsing.

### Error Handling

- Web scraping failures should be handled gracefully with user-friendly messages
- Use Rich console for colored error output
- Log detailed errors for debugging while showing simple messages to users

### Display Functions

All display functions use Rich library and should:

- Accept a list of Court objects as primary input
- Support optional source URL for data provenance
- Use consistent color schemes (green=available, red=unavailable, yellow=warnings)
- Include helpful summaries and statistics

## Testing Notes

- Tests focus primarily on the HTML extraction logic due to its complexity
- Web scraping components are harder to test due to external dependencies
- Use the `--save-data` flag to capture real HTML for test fixture creation
- Mock external requests in tests to avoid hitting the actual website

## Configuration

Project uses `pyproject.toml` for all configuration:

- Python 3.13+ required
- UV package manager recommended
- Ruff for linting and formatting
- MyPy for type checking
- Pytest for testing
