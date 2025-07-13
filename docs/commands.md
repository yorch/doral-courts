# Command Reference

Complete reference for all Doral Courts CLI commands.

## Global Options

These options are available for all commands:

- `--verbose, -v`: Enable verbose logging
- `--save-data`: Save retrieved HTML and JSON data to files
- `--help`: Show help message

## Commands Overview

### Core Commands

- [`list`](#list) - List available courts with filters
- [`list-courts`](#list-courts) - Show all court names
- [`list-locations`](#list-locations) - Show all locations
- [`list-available-slots`](#list-available-slots) - Show available time slots

### Data Commands

- [`slots`](#slots) - Detailed time slot availability
- [`data`](#data) - Comprehensive scraped data view
- [`history`](#history) - View historical court data

### Utility Commands

- [`watch`](#watch) - Monitor with real-time updates
- [`stats`](#stats) - Database statistics
- [`cleanup`](#cleanup) - Clean up old data

---

## `list`

List available courts with optional filters. Always fetches fresh data from website.

### Syntax

```bash
uv run doral-courts list [OPTIONS]
```

### Options

- `--sport [tennis|pickleball]`: Filter by sport type
- `--status [available|booked|maintenance]`: Filter by availability status
- `--date TEXT`: Date to check (default: today)

### Examples

```bash
# List all courts for today
uv run doral-courts list

# List tennis courts for tomorrow
uv run doral-courts list --sport tennis --date tomorrow

# List available courts for next week
uv run doral-courts list --status available --date +7

# Save data while listing
uv run doral-courts list --save-data --verbose
```

### Output

Displays a table with:

- Court Name
- Sport Type
- Date
- Time Slots (available/total)
- Status
- Capacity
- Price

---

## `list-courts`

List all available court names.

### Syntax

```bash
uv run doral-courts list-courts [OPTIONS]
```

### Options

- `--sport [tennis|pickleball]`: Filter by sport type
- `--date TEXT`: Date to check (default: today)

### Examples

```bash
# List all court names
uv run doral-courts list-courts

# List only tennis court names
uv run doral-courts list-courts --sport tennis

# List court names for specific date
uv run doral-courts list-courts --date 07/15/2025
```

### Output

Displays a numbered table of unique court names, optionally filtered by sport.

---

## `list-locations`

List all available locations with court counts.

### Syntax

```bash
uv run doral-courts list-locations [OPTIONS]
```

### Options

- `--sport [tennis|pickleball]`: Filter by sport type
- `--date TEXT`: Date to check (default: today)

### Examples

```bash
# List all locations
uv run doral-courts list-locations

# List locations with pickleball courts
uv run doral-courts list-locations --sport pickleball

# List locations for tomorrow
uv run doral-courts list-locations --date tomorrow
```

### Output

Displays a table with:

- Location name
- Number of courts at that location

---

## `list-available-slots`

List all available time slots by court for a specific date.

### Syntax

```bash
uv run doral-courts list-available-slots [OPTIONS]
```

### Options

- `--date TEXT`: Date to check (default: today)
- `--sport [tennis|pickleball]`: Filter by sport type
- `--location TEXT`: Filter by location

### Examples

```bash
# Show available slots for today
uv run doral-courts list-available-slots

# Show tennis slots for tomorrow
uv run doral-courts list-available-slots --date tomorrow --sport tennis

# Show slots at specific location
uv run doral-courts list-available-slots --location "Doral Central Park"
```

### Output

Displays:

- Summary statistics (total slots, courts, breakdown by sport/location)
- Detailed table grouped by time slots showing:
  - Time range
  - Court name
  - Sport type
  - Location
  - Capacity
  - Price

---

## `slots`

Show detailed time slot availability for courts. Always fetches fresh data.

### Syntax

```bash
uv run doral-courts slots [OPTIONS]
```

### Options

- `--court TEXT`: Show detailed time slots for a specific court
- `--date TEXT`: Date to check (default: today)
- `--available-only`: Show only available time slots

### Examples

```bash
# Show all time slots for today
uv run doral-courts slots

# Show slots for specific court
uv run doral-courts slots --court "DCP Tennis Court 1"

# Show only available slots for tomorrow
uv run doral-courts slots --date tomorrow --available-only
```

### Output

For each court, displays a table with:

- Start Time
- End Time
- Status (Available/Unavailable)

---

## `data`

Display comprehensive view of all scraped data from the website. Always fetches fresh data.

### Syntax

```bash
uv run doral-courts data [OPTIONS]
```

### Options

- `--mode [detailed|summary]`: Display mode (default: detailed)
- `--sport [tennis|pickleball]`: Filter by sport type
- `--date TEXT`: Date to check (default: today)

### Examples

```bash
# Show detailed data view
uv run doral-courts data

# Show summary of time slots
uv run doral-courts data --mode summary

# Show tennis data for specific date
uv run doral-courts data --sport tennis --date +3
```

### Output

**Detailed mode**: Complete information for each court including all fields and sample time slots

**Summary mode**: Analysis of time slots across all courts with statistics and popular time ranges

---

## `history`

View historical court data from database (cached data).

### Syntax

```bash
uv run doral-courts history [OPTIONS]
```

### Options

- `--sport [tennis|pickleball]`: Filter by sport type
- `--status [available|booked|maintenance]`: Filter by availability status
- `--date TEXT`: Date to check (default: today)
- `--mode [table|detailed|summary]`: Display mode (default: table)

### Examples

```bash
# Show historical data in table format
uv run doral-courts history

# Show detailed historical data for tennis
uv run doral-courts history --sport tennis --mode detailed

# Show summary for specific date
uv run doral-courts history --date yesterday --mode summary
```

### Output

Depends on mode:

- **table**: Simple court table
- **detailed**: Complete court information
- **summary**: Time slot analysis

---

## `watch`

Monitor court availability with real-time updates.

### Syntax

```bash
uv run doral-courts watch [OPTIONS]
```

### Options

- `--interval INTEGER`: Update interval in seconds (default: 300)
- `--sport [tennis|pickleball]`: Filter by sport type
- `--date TEXT`: Date to monitor (default: today)

### Examples

```bash
# Watch all courts, update every 5 minutes
uv run doral-courts watch

# Watch tennis courts, update every 2 minutes
uv run doral-courts watch --sport tennis --interval 120

# Watch courts for tomorrow
uv run doral-courts watch --date tomorrow
```

### Behavior

- Clears screen and shows updated data at each interval
- Press Ctrl+C to stop monitoring
- Shows last updated timestamp
- Saves data if `--save-data` flag is used

---

## `stats`

Show database statistics.

### Syntax

```bash
uv run doral-courts stats
```

### Output

Displays:

- Total courts in database
- Last updated timestamp
- Sport breakdown (tennis vs pickleball)
- Availability status breakdown

---

## `cleanup`

Clean up old court data.

### Syntax

```bash
uv run doral-courts cleanup [OPTIONS]
```

### Options

- `--days INTEGER`: Remove data older than N days (default: 7)

### Examples

```bash
# Remove data older than 7 days
uv run doral-courts cleanup

# Remove data older than 30 days
uv run doral-courts cleanup --days 30
```

### Output

Shows number of records removed from database.

---

## Common Patterns

### Combining Options

```bash
# Detailed tennis data with verbose logging and data export
uv run doral-courts data --sport tennis --mode detailed --verbose --save-data

# Watch pickleball courts at specific location
uv run doral-courts watch --sport pickleball --date tomorrow --interval 180
```

### Using with Shell Scripts

```bash
#!/bin/bash
# Check if tennis courts are available for tomorrow
uv run doral-courts list-available-slots --sport tennis --date tomorrow > tennis_slots.txt
```

### Error Handling

Most commands will show helpful error messages for:

- Invalid date formats
- Network connection issues
- Missing or invalid options
- Database errors

Use `--verbose` flag for detailed error information and debugging.
