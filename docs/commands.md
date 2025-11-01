# Command Quick Reference

Quick lookup for Doral Courts CLI commands. For comprehensive documentation with examples and detailed options, see the [Reference Guide](./reference.md#command-reference).

## Global Options

Available for all commands:

- `--verbose, -v` - Enable verbose logging
- `--save-data` - Save retrieved HTML/JSON data to files
- `--version` - Show version and exit
- `--help` - Show help message

## Core Commands

### Court Listing

```bash
# List all courts with filters
doral-courts list [--sport tennis|pickleball] [--status available|booked] [--date DATE] [--favorites]

# Show all court names
doral-courts list-courts [--sport tennis|pickleball]

# Show all locations with court counts
doral-courts list-locations [--sport tennis|pickleball]

# Show available time slots by court
doral-courts list-available-slots [--sport tennis|pickleball] [--date DATE]
```

📖 [Detailed documentation →](./reference.md#1-list---primary-court-listing)

### Data Analysis

```bash
# Detailed time slot availability
doral-courts slots --court "Court Name" [--date DATE] [--available-only]

# Comprehensive scraped data view
doral-courts data [--mode summary|detailed|raw] [--sport tennis|pickleball] [--date DATE]

# View historical court data (cached)
doral-courts history [--sport tennis|pickleball] [--date DATE] [--days N]
```

📖 [Detailed documentation →](./reference.md#2-slots---detailed-time-slot-view)

### Monitoring & Analytics

```bash
# Continuous background polling
doral-courts monitor [--interval N] [--sport tennis|pickleball] [--location "Location"] [--days-ahead N] [--quiet]

# Booking velocity and pattern analysis
doral-courts analyze [--sport tennis|pickleball] [--location "Location"] [--court "Court"] [--time-slot "8:00 am"] [--day-of-week Friday] [--days N] [--mode velocity|availability|summary]

# Real-time monitoring with updates
doral-courts watch [--interval N] [--sport tennis|pickleball]
```

📖 [Monitoring Guide →](./monitoring-guide.md) | [Command reference →](./reference.md#13-monitor---continuous-background-polling)

### Favorites & Queries

```bash
# Manage favorite courts
doral-courts favorites add "Court Name"
doral-courts favorites remove "Court Name"
doral-courts favorites list

# Run saved queries
doral-courts query list
doral-courts query run "query-name"
doral-courts query save "query-name" --sport tennis --date tomorrow
doral-courts query delete "query-name"
```

📖 [Detailed documentation →](./reference.md#11-favorites---favorite-courts-management)

### Database Management

```bash
# Show database statistics
doral-courts stats

# Clean up old data
doral-courts cleanup [--days N]
```

📖 [Detailed documentation →](./reference.md#9-stats---database-statistics)

## Common Usage Patterns

### Quick Checks

```bash
# What's available right now?
doral-courts list

# Tennis courts tomorrow
doral-courts list --sport tennis --date tomorrow

# Pickleball at specific location
doral-courts list --sport pickleball --location "Doral Legacy Park"
```

### Planning Ahead

```bash
# Check weekend availability (Saturday)
doral-courts list --date +6

# Monitor Friday morning slots
doral-courts monitor --sport pickleball --interval 5 --days-ahead 2 --quiet
```

### Analysis

```bash
# How fast do courts get booked?
doral-courts analyze --sport pickleball --day-of-week Friday --time-slot "8:00 am" --mode velocity

# Best day to find courts
doral-courts analyze --sport tennis --mode availability
```

## Date Format Options

- **Relative**: `today`, `tomorrow`, `yesterday`
- **Offset**: `+3` (3 days ahead), `-2` (2 days ago)
- **Absolute**: `07/15/2025`, `2025-07-15`

📖 [Date formats guide →](./date-formats.md)

## Getting Help

```bash
# Command-specific help
doral-courts list --help
doral-courts monitor --help
doral-courts analyze --help

# General help
doral-courts --help
```

## Documentation Index

- 📚 **[Reference Guide](./reference.md)** - Comprehensive command documentation with all options and examples
- 🎯 **[Usage Examples](./examples.md)** - Real-world use cases and workflows
- 📊 **[Monitoring Guide](./monitoring-guide.md)** - Continuous monitoring and booking analytics
- 📦 **[Installation Guide](./installation.md)** - Setup and configuration
- 🛠️ **[Development Guide](./development.md)** - Contributing and architecture

---

**Need more details?** See the [Reference Guide](./reference.md) for comprehensive documentation of all commands with full option lists, output formats, and detailed examples.
