# Date Formats Guide

The Doral Courts CLI supports flexible date input formats for all commands that accept a `--date` option.

## Default Behavior

If no `--date` option is provided, the command defaults to **today**.

## Supported Formats

### Relative Dates

These keywords are case-insensitive:

| Input       | Description   | Example Result (if today is 07/12/2025) |
| ----------- | ------------- | --------------------------------------- |
| `today`     | Current date  | 07/12/2025                              |
| `now`       | Same as today | 07/12/2025                              |
| `tomorrow`  | Next day      | 07/13/2025                              |
| `yesterday` | Previous day  | 07/11/2025                              |

### Offset Dates

Use `+` or `-` followed by a number to specify days relative to today:

| Input | Description        | Example Result (if today is 07/12/2025) |
| ----- | ------------------ | --------------------------------------- |
| `+1`  | 1 day from today   | 07/13/2025                              |
| `+7`  | 1 week from today  | 07/19/2025                              |
| `+30` | 30 days from today | 08/11/2025                              |
| `-1`  | 1 day ago          | 07/11/2025                              |
| `-7`  | 1 week ago         | 07/05/2025                              |
| `-30` | 30 days ago        | 06/12/2025                              |

### Absolute Dates

Multiple absolute date formats are supported:

| Format       | Description             | Example      |
| ------------ | ----------------------- | ------------ |
| `MM/DD/YYYY` | US format (recommended) | `07/15/2025` |
| `YYYY-MM-DD` | ISO format              | `2025-07-15` |
| `MM-DD-YYYY` | US format with dashes   | `07-15-2025` |
| `DD/MM/YYYY` | European format         | `15/07/2025` |
| `YYYY/MM/DD` | Alternative ISO format  | `2025/07/15` |

## Examples

### Basic Usage

```bash
# Default to today
uv run doral-courts list

# Explicit today
uv run doral-courts list --date today

# Tomorrow
uv run doral-courts list --date tomorrow

# Yesterday
uv run doral-courts list --date yesterday
```

### Offset Examples

```bash
# Next week
uv run doral-courts list --date +7

# 3 days from now
uv run doral-courts list-available-slots --date +3

# 2 days ago
uv run doral-courts history --date -2

# One month from now
uv run doral-courts watch --date +30
```

### Absolute Date Examples

```bash
# US format (recommended)
uv run doral-courts list --date 07/15/2025

# ISO format
uv run doral-courts slots --date 2025-07-15

# European format
uv run doral-courts data --date 15/07/2025
```

### Real-world Scenarios

```bash
# Check courts for the weekend
uv run doral-courts list-available-slots --date +5  # Friday
uv run doral-courts list-available-slots --date +6  # Saturday

# Monitor courts for next week
uv run doral-courts watch --date +7 --interval 300

# Historical analysis
uv run doral-courts history --date -7 --mode summary  # Last week
uv run doral-courts history --date -30 --mode detailed  # Last month

# Specific event planning
uv run doral-courts list --date 08/15/2025 --sport tennis
```

## Error Handling

### Invalid Formats

If you provide an invalid date format, the CLI will show a helpful error message:

```bash
$ uv run doral-courts list --date "invalid-date"
Error: Invalid date format: invalid-date. Supported formats: MM/DD/YYYY, today, tomorrow, yesterday, +N, -N
```

### Common Mistakes

| ❌ Incorrect  | ✅ Correct                    | Note                 |
| ------------ | ---------------------------- | -------------------- |
| `+7days`     | `+7`                         | No suffix needed     |
| `next week`  | `+7`                         | Use numeric offset   |
| `07/15/25`   | `07/15/2025`                 | Use 4-digit year     |
| `15-07-2025` | `07/15/2025` or `2025-07-15` | Use supported format |

## Tips

### Planning Ahead

```bash
# Check availability for the next two weeks
for i in {1..14}; do
  echo "Day +$i:"
  uv run doral-courts list-available-slots --date +$i --sport tennis | grep "Total Available"
done
```

### Date Validation

The CLI validates dates and will reject impossible dates:

```bash
$ uv run doral-courts list --date 02/30/2025
Error: Invalid date format: 02/30/2025. Use MM/DD/YYYY format.
```

### Timezone Considerations

- All dates are interpreted in the local system timezone
- The Doral reservation system uses Eastern Time (ET)
- Date calculations are based on calendar days, not 24-hour periods

## Integration with Commands

All commands that support `--date` use the same parsing logic:

### Core Commands

- `list --date tomorrow`
- `list-courts --date +7`
- `list-locations --date yesterday`
- `list-available-slots --date 07/15/2025`

### Data Commands

- `slots --date +3`
- `data --date 2025-08-01`
- `history --date -30`

### Monitoring

- `watch --date tomorrow`

This consistent date handling makes it easy to use the same date expressions across all commands.
