# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **`analyze` date ranges across year boundaries**: dates are now stored as ISO
  `YYYY-MM-DD` instead of `MM/DD/YYYY`, so `WHERE date BETWEEN ... AND ...` and
  `ORDER BY date` compare chronologically. Previously a range spanning a year
  boundary (e.g. late December to early January) could return no rows because
  `MM/DD/YYYY` text sorts `01/...` before `12/...`.

### Changed

- Court dates are stored canonically as ISO in the database and converted back
  to `MM/DD/YYYY` at the boundary, so `Court.date`, the scraper, and displays
  are unchanged. Court/slot ordering is now done in SQL.
- Existing databases are migrated in place on open (legacy `MM/DD/YYYY` values
  are rewritten to ISO), preserving historical tracking data.

## [0.2.0]

### Fixed

- **Deduplication**: courts are now keyed by `(name, date)` instead of
  `(name, date, time_slot)`, so re-scrapes update the existing row instead of
  inserting duplicates.
- **Orphaned time slots**: switched from `INSERT OR REPLACE` to
  `INSERT ... ON CONFLICT(name, date) DO UPDATE` (preserving the row id) and
  enabled `PRAGMA foreign_keys = ON` per SQLite connection.
- **PostgreSQL `cleanup`**: `clear_old_data` no longer uses SQLite-only SQL; the
  "older than N days" predicate is provided by each adapter.
- **Ordering**: courts and time slots are sorted chronologically (dates and
  12-hour times were previously compared lexicographically).
- **Scraper**: 4xx responses during session init are treated as failure; the
  CSRF token is fetched once per operation; debug HTML is written to a temp dir.
- **`analyze` on PostgreSQL**: queries now run through the database adapter and
  filters are parameterized (also removing a SQL-injection vector).

### Added

- Multiple database backends (SQLite, PostgreSQL) via the `db_adapter` layer,
  selected in `~/.doral-courts/config.yaml`.
- `DORAL_PG_PASSWORD` environment variable as a fallback for the PostgreSQL
  password (keeps secrets out of the config file).
- Schema migration that rebuilds the cache when the legacy unique key is found.
- Test suite for date parsing, database dedup/cleanup/migration, scraper
  pagination, display rendering, and CLI commands (24 → 97 tests; coverage
  13% → 66%).
- Tooling: `mypy` and `tests/` linting in CI, a coverage gate, a pre-commit
  config, and `G004` (no f-strings in logging).

### Changed

- Extracted the shared fetch → store → save workflow into
  `cli/_shared.py::fetch_and_store`, removing duplication across 8 commands.
- Backend detection uses an explicit adapter `dialect` instead of attribute
  sniffing; the codebase is now type-checked clean with mypy.
- Time-slot inserts are batched with `executemany`.
- The CLI `--version` string is read from installed package metadata.

## [0.1.0]

- Initial release: court scraping with Cloudflare bypass, SQLite storage,
  Rich CLI, filtering, historical tracking, and data export.
