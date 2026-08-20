# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0]

### Removed

- **Python 3.13 support.** `requires-python` is now `>=3.14`. Existing 3.13
  users must upgrade; the CLI is tested only against 3.14. Note that
  `core/scraper.py` now contains PEP 758 syntax (unparenthesized `except`
  groups), applied by `ruff format` under `target-version = "py314"`, so the
  file no longer parses on 3.13 at all.

### Added

- **Automated PyPI releases** via `.github/workflows/release.yml`, triggered by
  pushing a `v*` tag. Uses PyPI Trusted Publishing (OIDC), so no API token is
  stored in the repo. The job refuses to publish when the tag does not match
  the version in `pyproject.toml`, and re-runs lint, type checks, and tests
  before uploading. One-time PyPI setup is documented in
  `docs/development.md`.
- **Anti-bot failure classification.** `classify_anti_bot_response()` separates
  a Cloudflare WAF/IP block from a lost JavaScript challenge from plain rate
  limiting, and `Scraper.last_block` carries the result to the CLI. Previously
  every failure produced the same vague "the website may be blocking automated
  requests", which sends users chasing the wrong fix: a WAF block is an IP
  decision that no scraping library can bypass, while a lost challenge is the
  one case where a different bypass library would help.

### Changed

- **Python 3.14** is now the tested and required version: CI matrix, ruff
  `target-version`, mypy `python_version`, `.python-version`, and the trove
  classifier all move to 3.14.
- **`interpreter="native"` is pinned explicitly** when creating the cloudscraper
  session. This is already cloudscraper's default, but the fork
  `cloudscraper-enhanced` defaults to `js2py`, which raises
  `RuntimeError: Your python version made changes to the bytecode` on Python
  3.13+. The pin (and a test asserting it) prevents a future dependency swap
  from silently selecting a broken interpreter.
- `cloudscraper` stays at 1.2.71 — the newest release published under that
  name. The maintained fork was evaluated and rejected; see
  `docs/reference.md` and `AGENTS.md` for the reasoning.

### Changed (from the preceding dependency upgrade)

- **Dependencies upgraded to latest**, including four major bumps:
  `mypy` 1.x → 2.3.1, `rich` 14.x → 15.0.0, `pytest` 8.x → 9.1.1, and
  `pytest-cov` 6.x → 7.1.0. Also bumped `requests` 2.34.2,
  `beautifulsoup4` 4.15.0, `click` 8.4.2, `pyyaml` 6.0.3,
  `psycopg2-binary` 2.9.12, `ruff` 0.16.3, `pre-commit` 4.6.2, and the
  `hatchling` build requirement to 1.32.0. No source changes were needed:
  mypy 2.0's `--local-partial-types`/`--strict-bytes` default flips and
  ruff 0.16's expanded default rule set do not affect this codebase (an
  explicit `select` list overrides ruff's defaults).
- **CI actions upgraded**: `actions/checkout` v4 → v7,
  `actions/setup-python` v5 → v7, and `astral-sh/setup-uv` v4 → v10.0.1.
  `setup-uv` is pinned to an exact version because upstream stopped
  publishing floating major tags after v7.
- **`scripts/` is now linted in CI** (`ruff check`/`ruff format --check`),
  closing a gap where `pre-commit` checked those files but CI did not.
  `scripts/view_db.py` is formatted, fully annotated, and `T201` (`print`
  found) is ignored for `scripts/*` since it is a print-based inspection
  script.

## [0.2.1]

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
