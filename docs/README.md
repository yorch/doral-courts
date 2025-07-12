# Documentation Index

Welcome to the Doral Courts CLI documentation!

## 📖 Documentation Overview

This directory contains comprehensive documentation for the Doral Courts CLI application.

### Getting Started

1. **[Installation Guide](./installation.md)** - Setup instructions and requirements
2. **[Examples](./examples.md)** - Practical usage examples and common scenarios

### Reference

3. **[Command Reference](./commands.md)** - Complete documentation of all CLI commands
4. **[Date Formats](./date-formats.md)** - Supported date input formats and examples

### Development

5. **[Development Guide](./development.md)** - Contributing, architecture, and extending the application

## 🚀 Quick Navigation

### New Users

- Start with [Installation Guide](./installation.md)
- Try the [Examples](./examples.md) to see common usage patterns
- Reference [Date Formats](./date-formats.md) for flexible date input

### Regular Users

- Bookmark [Command Reference](./commands.md) for quick command lookup
- Check [Examples](./examples.md) for advanced usage patterns

### Developers

- Read [Development Guide](./development.md) for architecture and contribution guidelines
- See [Command Reference](./commands.md) for complete API understanding

## 💡 Quick Reference

### Most Common Commands

```bash
# List courts for today
uv run python main.py list

# Show court names
uv run python main.py list-courts

# Available slots for tomorrow
uv run python main.py list-available-slots --date tomorrow

# Monitor courts in real-time
uv run python main.py watch
```

### Key Features

- ✅ Flexible date handling (`today`, `tomorrow`, `+7`, `07/15/2025`)
- ✅ Sport filtering (`--sport tennis`, `--sport pickleball`)
- ✅ Location filtering (`--location "Doral Central Park"`)
- ✅ Real-time monitoring (`watch` command)
- ✅ Historical data (`history` command)
- ✅ Data export (`--save-data` flag)

## 📝 Documentation Structure

```
docs/
├── README.md           # This index file
├── installation.md     # Setup and installation
├── commands.md         # Complete command reference
├── examples.md         # Usage examples and scenarios
├── date-formats.md     # Date input format guide
└── development.md      # Development and contributing guide
```

## 🔗 External Links

- **Main README**: [../README.md](../README.md) - Project overview and quick start
- **Source Code**: Main application files in parent directory
- **Tests**: `test_html_extractor.py` - Unit tests for core functionality

## 🆘 Need Help?

1. **Installation Issues**: See [Installation Guide](./installation.md#troubleshooting)
2. **Command Help**: Run any command with `--help` flag
3. **Date Format Issues**: Check [Date Formats](./date-formats.md#error-handling)
4. **Development Questions**: See [Development Guide](./development.md)

## 📈 Documentation Updates

This documentation is updated with each release. If you find any issues or have suggestions:

1. Check the [Development Guide](./development.md) for contributing guidelines
2. Ensure you're using the latest version
3. Create an issue with details about the documentation problem

---

*Happy court hunting! 🎾*
