# Doral Courts CLI

A command-line interface for checking tennis and pickleball court availability in Doral, Florida.

## 🎾 Overview

The Doral Courts CLI is a Python application that scrapes court availability data from the Doral reservation system and provides an easy-to-use command-line interface for viewing court schedules, availability, and booking information.

## ✨ Features

- **Real-time Court Data**: Fetches fresh availability data from the Doral courts website
- **Multiple Sports**: Supports both tennis and pickleball courts
- **Flexible Date Handling**: Use relative dates like "today", "tomorrow", "+3", "-2"
- **Rich CLI Interface**: Beautiful tables and colored output using Rich library
- **Historical Data**: Local SQLite database for tracking court availability over time
- **Data Export**: Save HTML and JSON data for analysis
- **Watch Mode**: Monitor court availability with real-time updates
- **Comprehensive Filtering**: Filter by sport, location, status, and date

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yorch/doral-courts.git

# Install dependencies with uv
uv sync

# Or install with pip
pip install -r requirements.txt
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

## 📚 Documentation

For detailed documentation, see the [docs](./docs/) directory:

- **[Installation Guide](./docs/installation.md)** - Detailed setup instructions
- **[Command Reference](./docs/commands.md)** - Complete CLI command documentation
- **[Examples](./docs/examples.md)** - Common usage patterns and examples
- **[Date Formats](./docs/date-formats.md)** - Supported date input formats
- **[Development](./docs/development.md)** - Contributing and development setup

## 🔧 Available Commands

| Command                | Description                                 |
| ---------------------- | ------------------------------------------- |
| `list`                 | List available courts with filters          |
| `list-courts`          | Show all court names                        |
| `list-locations`       | Show all locations with court counts        |
| `list-available-slots` | Show available time slots by court          |
| `slots`                | Detailed time slot availability             |
| `data`                 | Comprehensive scraped data view             |
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

```bash
# Tennis courts for next week
uv run doral-courts list --sport tennis --date +7

# Pickleball courts at specific location
uv run doral-courts list --sport pickleball --location "Doral Central Park"

# Available slots for tomorrow with data export
uv run doral-courts list-available-slots --date tomorrow --save-data

# Watch tennis courts every 5 minutes
uv run doral-courts watch --sport tennis --interval 300
```

## 🗄️ Data Storage

- **Local Database**: SQLite database (`doral_courts.db`) stores historical data
- **Data Export**: HTML and JSON files saved to `data/` directory when using `--save-data`
- **Logging**: Configurable logging with `--verbose` flag

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

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## 🐛 Issues

If you encounter any issues or have feature requests, please [create an issue](link-to-issues).
