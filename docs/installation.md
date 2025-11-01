# Installation Guide

This guide covers different ways to install and set up the Doral Courts CLI application.

## Prerequisites

- Python 3.13 or higher
- Internet connection (for fetching court data)

## Installation Methods

### Method 1: Using uv (Recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager and project manager.

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/yorch/doral-courts.git

# Install dependencies and create virtual environment
uv sync

# Run the application
uv run doral-courts --help
```

### Method 2: Using pip and venv

```bash
# Clone the repository
git clone https://github.com/yorch/doral-courts.git

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
doral-courts --help
```

### Optional: PostgreSQL Support

By default, the application uses SQLite for data storage. For production deployments or high-frequency monitoring, you can install PostgreSQL support:

```bash
# Using uv
uv sync --extra postgresql

# Using pip
pip install -e .[postgresql]
# Or directly
pip install psycopg2-binary
```

See the [Monitoring Guide - Database Configuration](./monitoring-guide.md#database-configuration) for PostgreSQL setup instructions.

## Verification

After installation, verify everything works:

```bash
# Check if the CLI is working
uv run doral-courts --help

# Run tests to ensure everything is set up correctly
uv run pytest -v

# Test basic functionality
uv run doral-courts list-courts --help
```

## Configuration

### Environment Variables

The application doesn't require environment variables for basic usage, but you can configure:

- **Logging**: Use `--verbose` flag for detailed logging
- **Data Export**: Use `--save-data` flag to save HTML/JSON data

### Data Directory

The application creates the following directories:

- `data/` - Exported HTML and JSON files (created when using `--save-data`)
- `doral_courts.db` - SQLite database file for historical data (default)
  - Not created if using PostgreSQL backend
- `~/.doral-courts/config.yaml` - User configuration file (created on first run)

## Troubleshooting

### Common Issues

1. **Module not found errors**

   ```bash
   # Make sure you're in the virtual environment
   source .venv/bin/activate  # or use uv run
   ```

2. **Permission errors**

   ```bash
   # Make sure you have write permissions in the directory
   ls -la
   chmod +w .
   ```

3. **Network issues**

   ```bash
   # Test internet connectivity
   curl -I https://www.google.com
   ```

4. **Python version issues**

   ```bash
   # Check Python version
   python --version
   # Should be 3.13 or higher
   ```

### Getting Help

If you encounter issues:

1. Check the [examples documentation](./examples.md)
2. Run with verbose logging: `uv run doral-courts list --verbose`
3. Check the test suite: `uv run pytest -v`
4. Create an issue with error details and system information

## Development Setup

For development and contributing:

```bash
# Clone and set up as above, then:

# Install development dependencies
uv sync --group dev

# Run tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=src

# Code formatting (if you add tools)
uv run black .
uv run isort .
```

## Performance Notes

- First run may be slower as it fetches fresh data
- Subsequent runs use cached data when appropriate
- Use `--save-data` flag sparingly to avoid large data files
- Database grows over time; use `cleanup` command to manage size
