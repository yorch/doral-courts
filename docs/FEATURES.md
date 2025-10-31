# Doral Courts CLI - Complete Feature Documentation

**Version**: 0.1.0
**Last Updated**: 2025-10-31

## Table of Contents

- [Overview](#overview)
- [Core Features](#core-features)
- [Command Reference](#command-reference)
- [Data Management](#data-management)
- [Display & UI Features](#display--ui-features)
- [Technical Features](#technical-features)
- [Configuration & Options](#configuration--options)

---

## Overview

Doral Courts CLI is a Python-based command-line tool that provides real-time tennis and pickleball court availability for Doral, Florida. It scrapes data from the official Doral reservation system and presents it in a user-friendly, filterable format with historical tracking capabilities.

**Primary Use Cases**:

- Finding available tennis/pickleball courts for specific dates
- Monitoring court availability in real-time
- Tracking historical availability patterns
- Managing favorite courts for quick access
- Executing saved queries for common searches
- Exporting data for analysis
- Quick lookup of court names and locations

---

## Core Features

### 1. Web Scraping & Data Fetching

**Cloudflare Bypass**:

- Uses `cloudscraper` library to bypass Cloudflare anti-bot protection
- Automatic challenge solving and session management
- Browser header simulation for compatibility

**Pagination Handling**:

- Automatically fetches all pages of court data
- Duplicate detection prevents repeated entries
- Smart pagination logic stops when no new data is found

**CSRF Token Management**:

- Extracts and uses CSRF tokens for authenticated requests
- Session initialization with proper cookies

**Error Handling**:

- Graceful degradation when website is unavailable
- Timeout handling (30 seconds default)
- Network error recovery with detailed logging

### 2. Data Storage & History

**SQLite Database** (`doral_courts.db`):

- Automatic schema creation and migrations
- Historical tracking of court availability
- Unique constraints prevent duplicates
- Indexed for efficient querying (sport_type, date, availability_status)

**Schema**:

```sql
courts table:
- id, name, sport_type, location, capacity
- availability_status, date, time_slot, price
- last_updated timestamp

time_slots table (future expansion):
- id, court_id, start_time, end_time, status
```

**Data Persistence**:

- All fetched data automatically stored in database
- Historical queries don't hit the website
- Cleanup command removes old data (default: 7 days)

### 3. Flexible Date Handling

**Relative Dates**:

- `today`, `now` - Current date
- `tomorrow` - Next day
- `yesterday` - Previous day

**Offset Dates**:

- `+N` - N days from today (e.g., `+7` for next week)
- `-N` - N days before today (e.g., `-2` for 2 days ago)

**Absolute Dates**:

- `MM/DD/YYYY` - U.S. format (07/15/2025)
- `YYYY-MM-DD` - ISO format (2025-07-15)
- `MM-DD-YYYY` - Alternative format
- `DD/MM/YYYY` - European format
- `YYYY/MM/DD` - Alternative ISO

**Implementation**: `utils/date_utils.py:parse_date_input()`

### 4. Comprehensive Filtering

**Sport Type**:

- Tennis courts only: `--sport tennis`
- Pickleball courts only: `--sport pickleball`
- Default: Both sports

**Availability Status**:

- Available courts: `--status available`
- Booked courts: `--status booked`
- Maintenance: `--status maintenance`

**Location**:

- Filter by location name: `--location "Doral Central Park"`
- Substring matching (case-insensitive)

**Court Name**:

- Specific court lookup: `--court "DLP Tennis Court 1"`
- Substring matching for flexibility

**Date Range** (via cleanup):

- Remove data older than N days
- Default retention: 7 days

### 5. Configuration & Personalization

**Configuration File**: `~/.doral-courts/config.yaml`

**Favorite Courts**:

- Save frequently accessed courts for quick reference
- Highlighted with ⭐ emoji in all table displays
- Filter results to show only favorites with `--favorites` flag
- Management via `favorites` command group

**Saved Queries**:

- Pre-configure complex search filters
- Execute saved queries by name with `query` command
- Support all filter parameters (sport, date, status, location)
- Shareable configuration for team workflows

**Default Preferences**:

- Set default sport filter
- Configure default date offset
- Customize data retention policies

**Configuration Example**:

```yaml
favorites:
  courts:
    - DLP Tennis Court 1
    - DCP Tennis Court 1

queries:
  my_tennis:
    sport: tennis
    date: tomorrow
    status: available
  weekend_pickleball:
    sport: pickleball
    date: "+2"
    location: "Doral Central Park"

defaults:
  sport: null
  date_offset: 0
```

**Implementation**: `utils/config.py:Config`

---

## Command Reference

### 1. `list` - Primary Court Listing

**Purpose**: Display available courts in table format with fresh data

**Usage**:

```bash
doral-courts list [OPTIONS]
```

**Options**:

- `--sport [tennis|pickleball]` - Filter by sport type
- `--status [available|booked|maintenance]` - Filter by availability
- `--date TEXT` - Date to check (default: today)
- `--favorites` - Show only favorite courts

**Output**: Rich table with columns:

- Court Name
- Sport Type
- Date
- Time Slots (available/total)
- Status
- Capacity
- Price

**Example**:

```bash
doral-courts list --sport tennis --date tomorrow
doral-courts list --status available --date +7
doral-courts list --favorites  # Show only favorite courts
doral-courts list --favorites --sport tennis  # Favorite tennis courts
```

### 2. `slots` - Detailed Time Slot View

**Purpose**: Show granular time-by-time availability for courts

**Usage**:

```bash
doral-courts slots [OPTIONS]
```

**Options**:

- `--court TEXT` - Filter to specific court name
- `--date TEXT` - Date to check
- `--available-only` - Show only available slots

**Output**: Individual tables per court showing:

- Start Time (e.g., "8:00 am")
- End Time (e.g., "9:00 am")
- Status (Available/Unavailable, color-coded)

**Example**:

```bash
doral-courts slots --date tomorrow --available-only
doral-courts slots --court "DLP Tennis Court 1"
```

### 3. `list-available-slots` - Quick Availability Overview

**Purpose**: Fast overview of which courts have availability

**Usage**:

```bash
doral-courts list-available-slots [OPTIONS]
```

**Options**:

- `--date TEXT` - Date to check
- `--sport [tennis|pickleball]` - Filter by sport
- `--location TEXT` - Filter by location

**Output**: Table showing courts with available slots highlighted

**Example**:

```bash
doral-courts list-available-slots --date tomorrow --sport tennis
```

### 4. `list-courts` - Court Names List

**Purpose**: Simple list of all court names

**Usage**:

```bash
doral-courts list-courts [OPTIONS]
```

**Options**:

- `--sport [tennis|pickleball]` - Filter by sport
- `--date TEXT` - Date reference

**Output**: Simple list of court names for easy reference/scripting

**Example**:

```bash
doral-courts list-courts --sport pickleball
```

### 5. `list-locations` - Location Directory

**Purpose**: Show all locations with court counts

**Usage**:

```bash
doral-courts list-locations [OPTIONS]
```

**Options**:

- `--sport [tennis|pickleball]` - Filter by sport
- `--date TEXT` - Date reference

**Output**: List of locations with number of courts available at each

**Example**:

```bash
doral-courts list-locations --sport tennis
```

### 6. `data` - Comprehensive Data View

**Purpose**: Most detailed view of all scraped data

**Usage**:

```bash
doral-courts data [OPTIONS]
```

**Options**:

- `--mode [detailed|summary]` - Display mode (default: detailed)
- `--sport [tennis|pickleball]` - Filter by sport
- `--date TEXT` - Date to check

**Display Modes**:

- **detailed**: Full court information with all metadata
- **summary**: Time slots analysis and statistics

**Output**:

- Detailed mode: Rich panels with complete court data
- Summary mode: Statistical analysis of time slot availability

**Example**:

```bash
doral-courts data --mode summary --date tomorrow
doral-courts data --mode detailed --sport tennis
```

### 7. `history` - Historical Data Viewer

**Purpose**: View previously fetched data from database (no web scraping)

**Usage**:

```bash
doral-courts history [OPTIONS]
```

**Options**:

- `--sport [tennis|pickleball]` - Filter by sport
- `--status [available|booked|maintenance]` - Filter by status
- `--date TEXT` - Date to query
- `--mode [table|detailed|summary]` - Display format

**Key Difference**: Uses cached database data only, doesn't fetch fresh data

**Example**:

```bash
doral-courts history --date yesterday --mode summary
doral-courts history --sport tennis --date -7
```

### 8. `watch` - Real-Time Monitoring

**Purpose**: Continuously monitor court availability with auto-refresh

**Usage**:

```bash
doral-courts watch [OPTIONS]
```

**Options**:

- `--interval INTEGER` - Update interval in seconds (default: 300 = 5 min)
- `--sport [tennis|pickleball]` - Filter by sport
- `--date TEXT` - Date to monitor

**Behavior**:

- Clears screen and refreshes display at specified interval
- Shows last update timestamp
- Stores each update in database
- Press Ctrl+C to stop

**Example**:

```bash
doral-courts watch --interval 300 --sport tennis
doral-courts watch --interval 60 --date tomorrow
```

### 9. `stats` - Database Statistics

**Purpose**: Show database statistics and health

**Usage**:

```bash
doral-courts stats
```

**Output Panel**:

- Total Courts: Count of records in database
- Last Updated: Most recent data fetch timestamp
- Sport Breakdown: Count by tennis/pickleball
- Availability Status: Count by status type

**Example**:

```bash
doral-courts stats
```

### 10. `cleanup` - Data Maintenance

**Purpose**: Remove old data from database to manage storage

**Usage**:

```bash
doral-courts cleanup [OPTIONS]
```

**Options**:

- `--days INTEGER` - Remove data older than N days (default: 7)

**Output**: Confirmation message with count of removed records

**Example**:

```bash
doral-courts cleanup --days 30
doral-courts cleanup --days 1  # Remove all but today
```

### 11. `favorites` - Favorite Courts Management

**Purpose**: Save and manage frequently accessed courts for quick filtering

**Usage**:

```bash
doral-courts favorites [COMMAND]
```

**Subcommands**:

- `list` - Show all favorite courts
- `add <court_name>` - Add a court to favorites
- `remove <court_name>` - Remove a court from favorites

**Output**: Rich table with star emoji (⭐) for favorites display

**Storage**: Favorites stored in `~/.doral-courts/config.yaml`

**Integration**:

- Use `--favorites` flag with `list` command to filter results
- Favorite courts highlighted with ⭐ in all table displays

**Example**:

```bash
# Manage favorites
doral-courts favorites add "DLP Tennis Court 1"
doral-courts favorites add "DCP Tennis Court 1"
doral-courts favorites list

# Use favorites in filtering
doral-courts list --favorites --sport tennis
doral-courts list --favorites --date tomorrow

# Remove a favorite
doral-courts favorites remove "DLP Tennis Court 1"
```

### 12. `query` - Saved Query Execution

**Purpose**: Execute pre-configured queries with saved parameters

**Usage**:

```bash
doral-courts query <query_name>
```

**Configuration**: Define queries in `~/.doral-courts/config.yaml`

**Supported Parameters**:

- `sport` - Filter by sport type
- `date` - Date to check
- `status` - Availability status filter
- `location` - Location filter

**Behavior**:

- Fetches fresh data from website using saved parameters
- Displays available queries if requested query not found
- Shows parameters being executed for transparency

**Configuration Example**:

```yaml
queries:
  my_tennis:
    sport: tennis
    date: tomorrow
    status: available
  weekend_pickleball:
    sport: pickleball
    date: "+2"
    location: "Doral Central Park"
```

**Example**:

```bash
# Run saved query
doral-courts query my_tennis
doral-courts query weekend_pickleball

# Show available queries (when query not found)
doral-courts query nonexistent
```

---

## Data Management

### Automatic Storage

**All fetch commands automatically**:

1. Scrape fresh data from website
2. Parse HTML into Court objects
3. Store in SQLite database with timestamp
4. Display to user

**Benefits**:

- Historical tracking without manual intervention
- Offline querying via `history` command
- Data persistence across sessions

### Export Capabilities

**Global Flag**: `--save-data`

**Exports**:

1. **HTML Files**: Raw HTML response from website
   - Filename: `data/YYYY-MM-DD_HHMMSS_<command>.html`
   - Multiple pages concatenated with `<!-- PAGE BREAK -->`

2. **JSON Files**: Structured court data
   - Filename: `data/YYYY-MM-DD_HHMMSS_<command>.json`
   - Includes: source URL, timestamp, court array
   - Format:

   ```json
   {
     "source": "https://...",
     "timestamp": "2025-10-31T14:30:00",
     "courts": [...]
   }
   ```

**Example**:

```bash
doral-courts --save-data list --date tomorrow
# Creates: data/2025-10-31_143000_list.html
#          data/2025-10-31_143000_list.json
```

### Database Operations

**Location**: `doral_courts.db` (SQLite, current directory)

**Operations**:

- `insert_courts()`: Upsert court data (UNIQUE constraint on name+date+time_slot)
- `get_courts()`: Query with filters (sport, status, date)
- `get_stats()`: Aggregate statistics
- `clear_old_data()`: Delete records older than N days

**Schema Migrations**:

- Automatic migration from legacy `surface_type` to `capacity` column
- Maintains backward compatibility

---

## Display & UI Features

### Rich CLI Interface

**Library**: Rich (v14.0.0+)

**Features**:

- Color-coded output (green=available, red=unavailable, yellow=warnings)
- Unicode tables with borders
- Progress spinners during data fetching
- Panels for structured information
- Markdown rendering support

### Table Displays

**Main Court Table** (`display/tables.py`):

```
┏━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━┓
┃ Court Name  ┃ Sport ┃ Date  ┃ Slots  ┃ Status ┃ Cap   ┃ Price ┃
┡━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━┩
│ DLP Tennis  │ Ten   │ 11/01 │ 5/21   │ Avail  │ 3     │ $0.00 │
└─────────────┴───────┴───────┴────────┴────────┴───────┴───────┘
```

**Time Slots Table** (`slots` command):

```
┏━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Start Time ┃ End Time  ┃ Status      ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ 8:00 am    │ 9:00 am   │ Available   │
│ 9:00 am    │ 10:00 am  │ Unavailable │
└────────────┴───────────┴─────────────┘
```

### Progress Indicators

**Spinner with Description**:

```
⠋ Fetching court data...
⠙ Fetched 9 courts
```

**Watch Mode Updates**:

```
Last updated: 2025-10-31 14:30:00

[Court Table]

Next update in 300 seconds...
```

### Color Coding

**Status Colors**:

- 🟢 Green: Available, Success
- 🔴 Red: Unavailable, Errors
- 🟡 Yellow: Warnings, No data
- 🔵 Blue: Info messages
- ⚪ Dim: Timestamps, helper text

---

## Technical Features

### Architecture

**Modular Design**:

```
cli/          - Click command definitions
core/         - Business logic (scraper, database, parser)
display/      - UI formatting and rendering
utils/        - Shared utilities (logging, dates, files)
```

**Separation of Concerns**:

- Commands orchestrate workflow
- Core modules handle data operations
- Display modules format output
- Utils provide cross-cutting functionality

### HTML Parsing

**Parser**: `core/html_extractor.py:CourtAvailabilityHTMLExtractor`

**Capabilities**:

- BeautifulSoup4 for HTML parsing
- Extracts court metadata from search results
- Parses time slot availability from detail rows
- Handles missing/malformed data gracefully

**Data Models** (dataclasses):

```python
@dataclass
class Court:
    name: str
    sport_type: str
    location: str
    capacity: str
    availability_status: str
    date: str
    time_slots: List[TimeSlot]
    price: str

@dataclass
class TimeSlot:
    start_time: str
    end_time: str
    status: str
```

### Logging

**Logger**: `utils/logger.py`

**Levels**:

- DEBUG: Detailed diagnostic info (enabled with `--verbose`)
- INFO: General operational messages
- WARNING: Non-critical issues
- ERROR: Failures requiring attention

**Output**:

- Console: INFO and above
- Verbose mode: DEBUG and above
- Format: `YYYY-MM-DD HH:MM:SS - module - LEVEL - message`

**Example**:

```
2025-10-31 14:14:44 - doral_courts.core.scraper - INFO - Starting court data fetch
```

### Error Handling

**Graceful Degradation**:

- Network failures: Retry with exponential backoff (future)
- Missing data: Use default values
- Invalid dates: Clear error messages
- Website blocking: Informative user guidance

**User-Friendly Messages**:

```
❌ [red]Unable to fetch court data from website.[/red]
⚠️  [yellow]The website may be temporarily unavailable[/yellow]
ℹ️  [blue]Try running: doral-courts list[/blue]
```

### Performance

**Optimization**:

- Pagination stops when duplicates detected (>50%)
- Database indexing on common query fields
- Connection pooling for SQLite
- Cloudflare challenge caching

**Response Times** (approximate):

- First request: 8-12 seconds (Cloudflare challenge)
- Subsequent requests: 3-5 seconds
- Database queries: <100ms

---

## Configuration & Options

### Global Options

**Available for all commands**:

`--verbose, -v`

- Enable detailed DEBUG logging
- Shows all network requests, SQL queries, parsing steps
- Helpful for troubleshooting

`--save-data`

- Export HTML and JSON to `data/` directory
- Includes timestamp in filename
- Preserves raw data for analysis

`--version`

- Show version and exit
- Current: 0.1.0

`--help`

- Show command help message
- Available for main CLI and each subcommand

### Environment Variables

**None currently supported** (future enhancement)

Potential future variables:

- `DORAL_COURTS_DB_PATH` - Custom database location
- `DORAL_COURTS_DATA_DIR` - Custom export directory
- `DORAL_COURTS_TIMEOUT` - Request timeout override

### Configuration Files

**None currently supported** (future enhancement)

Potential future config:

- `~/.doral-courts/config.yaml` - User preferences
- Default sport, date offset, refresh interval
- Notification settings, filters

---

## Data Formats

### Court Data Structure

**JSON Export Format**:

```json
{
  "source": "https://fldoralweb.myvscloud.com/webtrac/web/search.html?...",
  "timestamp": "2025-10-31T14:30:00",
  "courts": [
    {
      "name": "DLP Tennis Court 1",
      "sport_type": "Tennis",
      "location": "Doral Central Park",
      "capacity": "3",
      "availability_status": "Available",
      "date": "11/01/2025",
      "time_slots": [
        {
          "start_time": "8:00 am",
          "end_time": "9:00 am",
          "status": "Available"
        }
      ],
      "price": "$0.00/hour"
    }
  ]
}
```

### Database Schema

**SQLite Tables**:

```sql
-- Main court records
CREATE TABLE courts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sport_type TEXT NOT NULL,
    location TEXT NOT NULL,
    capacity TEXT NOT NULL,
    availability_status TEXT NOT NULL,
    date TEXT NOT NULL,
    time_slot TEXT NOT NULL,  -- Aggregated slot info
    price TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, date, time_slot)
);

-- Indexes for efficient querying
CREATE INDEX idx_sport_type ON courts(sport_type);
CREATE INDEX idx_availability ON courts(availability_status);
CREATE INDEX idx_date ON courts(date);
```

---

## Integration Points

### Command Chaining

**Example workflows**:

```bash
# Fetch and save data, then view stats
doral-courts --save-data list --date tomorrow
doral-courts stats

# Monitor availability and export data periodically
doral-courts --save-data watch --interval 300 --sport tennis
```

### Scripting Support

**Exit Codes**:

- 0: Success
- 1: General error (network, parsing, invalid input)

**Scriptable Commands**:

```bash
# Get court names for scripting
courts=$(doral-courts list-courts --sport tennis)

# Check if specific court available
doral-courts slots --court "DLP Tennis Court 1" --available-only
```

### Data Pipeline

**Typical flow**:

1. `list` command → Fetch & store
2. Database → Historical data accumulation
3. `history` command → Query trends
4. `cleanup` command → Maintain storage
5. Export → Analysis in other tools (Python, R, Excel)

---

## Dependencies

### Production Dependencies

- **requests** (>=2.32.0): HTTP library for web requests
- **beautifulsoup4** (>=4.13.0): HTML parsing
- **click** (>=8.2.0): CLI framework
- **rich** (>=14.0.0): Terminal formatting
- **cloudscraper** (>=1.2.0): Cloudflare bypass

### Development Dependencies

- **pytest** (>=8.4.1): Testing framework
- **ruff** (>=0.1.0): Linting and formatting
- **mypy** (>=1.8.0): Type checking
- **black** (>=23.0.0): Code formatting
- **pre-commit** (>=3.0.0): Git hooks

---

## Known Limitations

### Current Limitations

1. **Single Website Support**: Only works with Doral reservation system
2. **No Booking**: Read-only, cannot make reservations
3. **No Notifications**: No alerts when courts become available
4. **No API**: CLI only, no REST/GraphQL API
5. **Limited Analytics**: Basic stats only, no trend analysis
6. **No Multi-User**: No user accounts or saved preferences
7. **No Mobile**: CLI only, no mobile app
8. **Rate Limiting**: No built-in protection against excessive requests
9. **Single Session**: Watch mode requires terminal to stay open

### Website Dependencies

**Fragile to changes**:

- HTML structure changes break parser
- Cloudflare protection updates may cause failures
- Website downtime = no data

**Workarounds**:

- Historical data via `history` command
- Exported JSON files as backup

---

## Performance Characteristics

### Benchmarks (Approximate)

**Command Execution Times**:

- `list`: 8-12s (first run), 3-5s (subsequent)
- `slots`: 8-12s (fetches all courts)
- `history`: <1s (database query only)
- `stats`: <100ms (simple aggregation)
- `watch` refresh: 3-5s per interval

**Data Sizes**:

- Single day data: ~50-100 KB
- Database: ~1 MB per week
- Exported HTML: ~200 KB per fetch
- Exported JSON: ~50 KB per fetch

**Resource Usage**:

- Memory: <50 MB during execution
- Disk: ~5-10 MB per week (database + exports)
- Network: ~200 KB per fetch

---

## Testing

### Test Coverage

**Current test focus**:

- HTML extraction logic (primary focus)
- Date parsing utilities
- Display formatting

**Not yet covered**:

- Web scraping (external dependency)
- Database operations (integration tests needed)
- CLI commands (end-to-end tests needed)

**Running tests**:

```bash
# All tests
uv run pytest -v

# With coverage
uv run pytest --cov=src

# Specific test
uv run pytest tests/unit/test_html_extractor.py -v
```

---

## Version History

### v0.1.0 (2025-10-31)

- Initial release
- 10 commands implemented
- Cloudflare bypass working
- SQLite database storage
- Rich CLI interface
- Flexible date handling
- Data export capabilities
- Watch mode for monitoring
- Comprehensive filtering

---

## Future Roadmap

See `FEATURE_IMPROVEMENTS.md` for detailed proposals on:

- Notifications and alerts
- Advanced analytics
- API and integrations
- Mobile/web interfaces
- Multi-city support
- Booking capabilities
