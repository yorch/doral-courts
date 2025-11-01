# Documentation Index

Welcome to the Doral Courts CLI documentation!

## 📖 Documentation Overview

Comprehensive documentation for the Doral Courts CLI application.

### Getting Started

1. **[Installation Guide](./installation.md)** - Setup, requirements, and PostgreSQL configuration
2. **[Examples](./examples.md)** - Practical usage examples and common scenarios
3. **[Command Quick Reference](./commands.md)** - Quick command syntax lookup

### Core Documentation

4. **[Reference Guide](./reference.md)** - Comprehensive technical reference for all features and commands
5. **[Monitoring Guide](./monitoring-guide.md)** 🆕 - Continuous monitoring and booking analytics
6. **[Date Formats](./date-formats.md)** - Supported date input formats and examples

### Development

7. **[Development Guide](./development.md)** - Architecture, contributing, and extending the application
8. **[Feature Roadmap](./feature-improvements.md)** - Planned enhancements and improvements

## 🚀 Quick Navigation

### New Users

Start here → [Installation Guide](./installation.md) → [Examples](./examples.md) → [Commands Quick Reference](./commands.md)

### Regular Users

- 📝 **Quick lookup**: [Command Quick Reference](./commands.md)
- 🎯 **Use cases**: [Examples](./examples.md)
- 📊 **Analytics**: [Monitoring Guide](./monitoring-guide.md)
- 📚 **Full reference**: [Reference Guide](./reference.md)

### Developers

- 🏗️ **Architecture**: [Development Guide](./development.md)
- 📋 **Roadmap**: [Feature Roadmap](./feature-improvements.md)
- 📖 **API reference**: [Reference Guide](./reference.md)

## 💡 Quick Reference

### Most Common Commands

```bash
# Check what's available now
doral-courts list

# Tennis courts tomorrow
doral-courts list --sport tennis --date tomorrow

# Monitor for historical data
doral-courts monitor --interval 10 --quiet

# Analyze booking patterns
doral-courts analyze --sport pickleball --mode velocity
```

### Key Features

- ✅ **Flexible dates**: `today`, `tomorrow`, `+7`, `2025-07-15`
- ✅ **Sport filtering**: `--sport tennis|pickleball`
- ✅ **Location filtering**: `--location "Doral Central Park"`
- ✅ **Continuous monitoring**: Background polling for analytics
- ✅ **Booking analytics**: Velocity and availability patterns
- ✅ **Database options**: SQLite (default) or PostgreSQL
- ✅ **Favorites & queries**: Save frequently used searches

## 📝 Documentation Structure

```
docs/
├── README.md              # This index file
├── installation.md        # Setup and installation
├── commands.md            # Quick command reference
├── reference.md           # Comprehensive technical reference
├── monitoring-guide.md    # Continuous monitoring & analytics
├── examples.md            # Usage examples and scenarios
├── date-formats.md        # Date input format guide
├── development.md         # Development and contributing
└── feature-improvements.md # Roadmap and planned features
```

## 🔗 External Resources

- **[Main README](../README.md)** - Project overview and quick start
- **[GitHub Repository](https://github.com/yorch/doral-courts)** - Source code and issues

## 🆘 Getting Help

1. **Installation issues**: [Installation Guide - Troubleshooting](./installation.md#troubleshooting)
2. **Command help**: Run any command with `--help` flag
3. **Monitoring setup**: [Monitoring Guide](./monitoring-guide.md#quick-start)
4. **Database configuration**: [Monitoring Guide - Database Configuration](./monitoring-guide.md#database-configuration)
5. **Development questions**: [Development Guide](./development.md)

## 🎯 Documentation by Use Case

### I want to

- **...check court availability** → [Examples - Quick Start](./examples.md#quick-start-examples)
- **...track booking patterns** → [Monitoring Guide](./monitoring-guide.md)
- **...use PostgreSQL instead of SQLite** → [Monitoring Guide - Database Configuration](./monitoring-guide.md#database-configuration)
- **...save favorite courts** → [Reference - Favorites](./reference.md#11-favorites---favorite-courts-management)
- **...understand all commands** → [Reference Guide](./reference.md#command-reference)
- **...contribute code** → [Development Guide](./development.md)
