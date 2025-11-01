# Doral Courts CLI

A command-line interface for checking tennis and pickleball court availability in Doral, Florida.

## 🎾 Overview

The Doral Courts CLI is a Python application that scrapes court availability data from the Doral reservation system and provides an easy-to-use command-line interface for viewing court schedules, availability, and booking information.

## ✨ Features

- **Real-time Court Data**: Fetches fresh availability data from the Doral courts website
- **Multiple Sports**: Supports both tennis and pickleball courts
- **Flexible Date Handling**: Use relative dates like "today", "tomorrow", "+3", "-2"
- **Rich CLI Interface**: Beautiful tables and colored output using Rich library
- **Favorite Courts**: Save and filter your frequently used courts with quick access
- **Saved Queries**: Store commonly used search filters for instant access
- **Historical Data**: Database storage (SQLite or PostgreSQL) for tracking court availability over time
- **Continuous Monitoring**: Background polling to build historical booking patterns
- **Booking Analytics**: Analyze booking velocity and availability trends
- **Data Export**: Save HTML and JSON data for analysis
- **Watch Mode**: Monitor court availability with real-time updates
- **Comprehensive Filtering**: Filter by sport, location, status, and date

## 🚀 Quick Start

### Requirements

- Python 3.13 or higher
- Internet connection for fetching court data

### Installation

```bash
# Clone the repository
git clone https://github.com/yorch/doral-courts.git
cd doral-courts

# Install dependencies with uv (recommended)
uv sync

# Or install with pip
pip install -r requirements.txt

# Optional: Install with PostgreSQL support for production use
uv sync --extra postgresql
# Or with pip
pip install -e .[postgresql]
```

### Basic Usage

```bash
# List all available courts for today
uv run doral-courts list

# Show available time slots for tomorrow
uv run doral-courts list-available-slots --date tomorrow

# List all court names
uv run doral-courts list-courts

# Show locations with court counts
uv run doral-courts list-locations

# Watch for real-time updates
uv run doral-courts watch --interval 300
```

## 📊 Key Use Cases

### 1. Check Current Availability

Perfect for finding courts right now or in the near future.

```bash
doral-courts list --sport tennis --date tomorrow
```

### 2. Track Booking Patterns

Understand when courts get booked to plan your reservations strategically.

```bash
# Start monitoring
doral-courts monitor --sport pickleball --interval 10 --quiet &

# Analyze after 2-4 weeks
doral-courts analyze --day-of-week Friday --time-slot "8:00 am" --mode velocity
```

### 3. Save Favorite Searches

Quick access to your regular court searches.

```bash
doral-courts query save weekend_tennis --sport tennis --date +6
doral-courts query run weekend_tennis
```

## 📚 Documentation

For detailed documentation, see the [docs](./docs/) directory:

**Getting Started:**

- **[Installation Guide](./docs/installation.md)** - Setup, requirements, and PostgreSQL configuration
- **[Examples](./docs/examples.md)** - Common usage patterns and real-world scenarios
- **[Command Quick Reference](./docs/commands.md)** - Quick syntax lookup

**Features & Reference:**

- **[Reference Guide](./docs/reference.md)** - Comprehensive technical documentation
- **[Monitoring Guide](./docs/monitoring-guide.md)** - 🆕 Continuous monitoring and booking analytics
- **[Date Formats](./docs/date-formats.md)** - Supported date input formats

**Development:**

- **[Development Guide](./docs/development.md)** - Architecture and contributing
- **[Feature Roadmap](./docs/feature-improvements.md)** - Planned enhancements

## 🔧 Available Commands

| Command                | Description                                 |
| ---------------------- | ------------------------------------------- |
| `list`                 | List available courts with filters          |
| `list-courts`          | Show all court names                        |
| `list-locations`       | Show all locations with court counts        |
| `list-available-slots` | Show available time slots by court          |
| `slots`                | Detailed time slot availability             |
| `data`                 | Comprehensive scraped data view             |
| `favorites`            | Manage favorite courts (add/remove/list)    |
| `query`                | Run saved queries by name                   |
| `monitor`              | Continuous background polling for analytics |
| `analyze`              | Booking velocity and pattern analysis       |
| `history`              | View historical court data                  |
| `watch`                | Monitor availability with real-time updates |
| `stats`                | Database statistics                         |
| `cleanup`              | Clean up old data                           |

## 📅 Date Formats

The CLI supports flexible date input:

- **Relative**: `today`, `tomorrow`, `yesterday`
- **Offset**: `+3` (3 days from today), `-2` (2 days ago)
- **Absolute**: `07/15/2025`, `2025-07-15`

## 🎯 Examples

### Quick Checks

```bash
# What's available right now?
uv run doral-courts list

# Tennis courts for next week
uv run doral-courts list --sport tennis --date +7

# Pickleball courts at specific location
uv run doral-courts list --sport pickleball --location "Doral Central Park"

# Available slots for tomorrow with data export
uv run doral-courts list-available-slots --date tomorrow --save-data

# Watch tennis courts every 5 minutes
uv run doral-courts watch --sport tennis --interval 300
```

### Favorites & Saved Queries

```bash
# Manage favorite courts
uv run doral-courts favorites add "DLP Tennis Court 1"
uv run doral-courts favorites list
uv run doral-courts list --favorites  # Show only favorite courts

# Run a saved query
uv run doral-courts query save my_tennis --sport tennis --date tomorrow
uv run doral-courts query run my_tennis
```

### Monitoring & Analytics

Track booking patterns to answer questions like "How fast do Friday 8am pickleball courts get booked?"

```bash
# 1. Start continuous monitoring (runs in background)
nohup uv run doral-courts monitor --sport pickleball --interval 10 --quiet > monitor.log 2>&1 &

# 2. Let it collect data for 2-4 weeks

# 3. Analyze booking velocity
uv run doral-courts analyze --sport pickleball --day-of-week Friday --time-slot "8:00 am" --mode velocity

# 4. Check which days have best availability
uv run doral-courts analyze --sport tennis --mode availability
```

See the [Monitoring Guide](./docs/monitoring-guide.md) for detailed analytics workflows.

## 🗄️ Data Storage

### Database Options

**SQLite (Default)**:

- Local file-based database: `doral_courts.db`
- No additional setup required
- Perfect for personal use

**PostgreSQL (Optional)**:

- For production deployments and high-frequency monitoring
- Better performance with concurrent access
- Requires separate installation (see [Monitoring Guide](./docs/monitoring-guide.md#database-configuration))

### Other Storage

- **Data Export**: HTML and JSON files saved to `data/` directory when using `--save-data`
- **Configuration**: User settings in `~/.doral-courts/config.yaml`
- **Logging**: Configurable with `--verbose` flag

## ⚙️ Configuration

The CLI stores user preferences in `~/.doral-courts/config.yaml`. This file is automatically created on first use.

**Favorite Courts**:

```yaml
favorites:
  courts:
    - DLP Tennis Court 1
    - DCP Tennis Court 1
```

**Saved Queries**:

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

**Defaults**:

```yaml
defaults:
  sport: null        # Default sport filter
  date_offset: 0     # Default date offset (0 = today)
```

**Database Configuration**:

```yaml
database:
  type: sqlite  # or 'postgresql' for production
  sqlite:
    path: doral_courts.db
  # postgresql:  # Uncomment for PostgreSQL
  #   host: localhost
  #   port: 5432
  #   database: doral_courts
  #   user: your_user
  #   password: your_password
```

See [Monitoring Guide - Database Configuration](./docs/monitoring-guide.md#database-configuration) for PostgreSQL setup.

## 🛠️ Development

### Running Tests

```bash
# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=src
```

### Project Structure

```
doral-courts/
├── src/
│   └── doral_courts/    # Main package
│       ├── cli/         # CLI commands and entry point
│       ├── core/        # Core business logic (scraper, database, html_extractor)
│       ├── display/     # UI formatting and display utilities
│       └── utils/       # Utility functions (logging, dates, files)
├── tests/               # Test suite
├── docs/                # Documentation
├── data/                # Exported data files
└── pyproject.toml       # Project configuration and dependencies
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! See the [Development Guide](./docs/development.md) for details on:

- Project architecture and code structure
- Setting up your development environment
- Running tests and code quality tools
- Submitting pull requests

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## 🐛 Issues & Support

**Found a bug or have a feature request?**

- Check [existing issues](https://github.com/yorch/doral-courts/issues) first
- [Create a new issue](https://github.com/yorch/doral-courts/issues/new) with:
  - Clear description of the problem/feature
  - Steps to reproduce (for bugs)
  - Your environment details (Python version, OS)

**Need help?**

- Review the [Documentation Index](./docs/README.md)
- Check [Examples](./docs/examples.md) for common use cases
- See [Troubleshooting](./docs/installation.md#troubleshooting) section
