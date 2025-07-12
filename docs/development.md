# Development Guide

Guide for developers who want to contribute to or extend the Doral Courts CLI.

## Architecture Overview

The application follows a modular architecture with clear separation of concerns:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   main.py       │    │   scraper.py     │    │ html_extractor. │
│   (CLI Interface)│───▶│   (Web Scraping) │───▶│ py (HTML Parse) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                                              │
         ▼                                              ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   utils.py      │    │   database.py    │    │   logger.py     │
│   (Display)     │    │   (Data Storage) │    │   (Logging)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Core Components

### main.py

- CLI entry point using Click framework
- Command definitions and argument parsing
- Orchestrates other components
- Handles global options (verbose, save-data)

### scraper.py

- Web scraping using cloudscraper (Cloudflare bypass)
- HTTP request handling
- Rate limiting and retry logic
- URL management

### html_extractor.py

- BeautifulSoup-based HTML parsing
- Data model definitions (Court, TimeSlot dataclasses)
- Court availability detection logic
- Time slot extraction

### database.py

- SQLite database operations
- Historical data storage
- Data migration handling
- Query interface

### utils.py

- Display functions using Rich library
- Data export functionality (HTML/JSON)
- Date parsing logic
- Formatting utilities

### logger.py

- Centralized logging configuration
- Configurable log levels
- File and console output

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
uv run python -m pytest test_html_extractor.py -v
uv run python main.py --help
```

### Development Dependencies

```toml
[dependency-groups]
dev = [
    "pytest>=8.4.1",
    # Add other dev tools as needed
    # "black",
    # "isort",
    # "mypy",
    # "coverage",
]
```

## Code Style

### General Guidelines

- Follow PEP 8 style guidelines
- Use type hints where possible
- Write docstrings for functions and classes
- Keep functions focused and small
- Use meaningful variable names

### Naming Conventions

- Files: `snake_case.py`
- Functions: `snake_case()`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`
- Variables: `snake_case`

### Example Code Style

```python
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Court:
    """Represents a court with its availability information."""
    name: str
    sport_type: str
    location: str
    capacity: str
    availability_status: str
    date: str
    time_slots: List[TimeSlot]
    price: Optional[str] = None

def parse_date_input(date_input: Optional[str] = None) -> str:
    """
    Parse date input supporting both absolute and relative formats.

    Args:
        date_input: Date string in various formats

    Returns:
        Date string in MM/DD/YYYY format

    Raises:
        ValueError: If date format is invalid
    """
    if date_input is None:
        return datetime.now().strftime("%m/%d/%Y")
    # ... implementation
```

## Testing

### Test Structure

Tests are located in `test_html_extractor.py` and cover:

- HTML parsing functionality
- Data extraction logic
- Error handling
- Edge cases

### Running Tests

```bash
# Run all tests
uv run python -m pytest test_html_extractor.py -v

# Run with coverage
uv run python -m pytest --cov=. test_html_extractor.py

# Run specific test
uv run python -m pytest test_html_extractor.py::TestCourtAvailabilityHTMLExtractor::test_parse_court_data_single_court -v
```

### Writing Tests

```python
def test_new_feature(self):
    """Test description of what this test covers."""
    # Arrange
    html = """<html>...</html>"""
    soup = BeautifulSoup(html, 'html.parser')

    # Act
    result = self.extractor.parse_court_data(soup)

    # Assert
    self.assertEqual(len(result), 1)
    self.assertEqual(result[0].name, "Expected Name")
```

### Test Guidelines

- Test both happy path and edge cases
- Use descriptive test names
- Include docstrings for complex tests
- Mock external dependencies
- Test error conditions

## Adding New Features

### Adding a New Command

1. **Define the command in main.py**:

```python
@cli.command(name='new-command')
@click.option('--option', help='Description')
@click.pass_context
def new_command(ctx, option: Optional[str]):
    """Command description."""
    # Implementation
```

2. **Add utility functions in utils.py**:

```python
def display_new_data(data: List[Any]) -> None:
    """Display function for new command."""
    # Implementation using Rich tables/panels
```

3. **Update imports**:

```python
from utils import ..., display_new_data
```

4. **Add tests**:

```python
def test_new_command_functionality(self):
    """Test the new command works correctly."""
    # Test implementation
```

### Adding New Data Fields

1. **Update the dataclass in html_extractor.py**:

```python
@dataclass
class Court:
    # ... existing fields
    new_field: str
```

2. **Update parsing logic**:

```python
def parse_court_data(self, soup: BeautifulSoup) -> List[Court]:
    # ... existing parsing
    new_field = cell.find('td', {'data-title': 'New Field'})
    new_field_value = new_field.get_text(strip=True) if new_field else "Default"
```

3. **Update database schema in database.py**:

```python
def init_database(self):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courts (
            -- existing columns
            new_field TEXT,
            -- ...
        )
    ''')

    # Add migration logic if needed
```

4. **Update display functions in utils.py**:

```python
def display_courts_table(courts: List[Court]):
    table.add_column("New Field", style="blue")
    # ...
    table.add_row(
        # ... existing columns
        court.new_field
    )
```

### Adding New Date Formats

1. **Update parse_date_input in utils.py**:

```python
def parse_date_input(date_input: Optional[str] = None) -> str:
    # Add new format to common_formats list
    common_formats = [
        "%Y-%m-%d",
        "%m-%d-%Y",
        # ... existing formats
        "%d.%m.%Y",  # New format: DD.MM.YYYY
    ]
```

2. **Update documentation**:

- Add to `docs/date-formats.md`
- Update help text in command options
- Add examples

## Debugging

### Logging

```python
# Add debug logging
logger.debug(f"Processing court: {court_name}")
logger.info(f"Found {len(courts)} courts")
logger.warning("Unexpected HTML structure")
logger.error(f"Failed to parse: {error}")
```

### Verbose Mode

Run commands with `--verbose` flag for detailed logging:

```bash
uv run python main.py list --verbose
```

### Data Inspection

Save data for inspection:

```bash
uv run python main.py data --save-data
# Check data/ directory for HTML and JSON files
```

### Database Inspection

```python
# Debug database content
uv run python -c "
from database import Database
db = Database()
stats = db.get_stats()
print(stats)
"
```

## Performance Considerations

### Web Scraping

- Use cloudscraper to handle Cloudflare protection
- Implement reasonable delays between requests
- Cache data locally when possible
- Handle network errors gracefully

### Database Operations

- Use batch inserts for multiple records
- Index frequently queried columns
- Clean up old data periodically
- Use transactions for consistency

### Memory Usage

- Process data in chunks for large datasets
- Avoid keeping large HTML strings in memory
- Use generators for large result sets

## Error Handling

### Network Errors

```python
try:
    response = scraper.fetch_data()
except requests.RequestException as e:
    logger.error(f"Network error: {e}")
    console.print("[red]Unable to fetch data from website.[/red]")
    return
```

### HTML Parsing Errors

```python
try:
    courts = extractor.parse_court_data(soup)
except Exception as e:
    logger.warning(f"Error parsing court data: {e}")
    # Continue processing or return empty list
```

### Date Parsing Errors

```python
try:
    parsed_date = parse_date_input(date)
except ValueError as e:
    console.print(f"[red]Error: {e}[/red]")
    return
```

## Release Process

### Version Management

Update version in `pyproject.toml`:

```toml
[project]
version = "0.2.0"
```

### Testing Before Release

```bash
# Run full test suite
uv run python -m pytest test_html_extractor.py -v

# Test all commands
uv run python main.py --help
uv run python main.py list-courts --help
# ... test other commands

# Test with real data
uv run python main.py list --verbose
```

### Documentation Updates

- Update README.md with new features
- Add examples to docs/examples.md
- Update command reference in docs/commands.md
- Update date formats if changed

## Contributing Guidelines

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Update documentation
6. Submit pull request with clear description

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] Error handling is appropriate
- [ ] Performance impact is considered
- [ ] Backwards compatibility is maintained

### Commit Messages

Use clear, descriptive commit messages:

```
Add list-courts command for displaying court names

- Implements new CLI command to show unique court names
- Supports sport filtering option
- Includes comprehensive help text and examples
- Adds utility function display_courts_list()
```

## Extending the Application

### Adding New Data Sources

1. Create new scraper module
2. Implement common interface
3. Update main.py to support multiple sources
4. Add configuration options

### Integration with Other Systems

1. Add export formats (CSV, XML, etc.)
2. Implement webhook notifications
3. Add API endpoint wrappers
4. Create calendar integration

### UI Enhancements

1. Add more Rich formatting options
2. Implement interactive mode
3. Add progress bars for long operations
4. Create configuration file support

This development guide should help you understand the codebase and contribute effectively to the project.
