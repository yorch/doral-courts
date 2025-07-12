# Usage Examples

Practical examples and common use cases for the Doral Courts CLI.

## Quick Start Examples

### Check What's Available Right Now

```bash
# See all courts for today
uv run python main.py list

# Just the court names
uv run python main.py list-courts

# Available time slots for today
uv run python main.py list-available-slots
```

### Plan for Tomorrow

```bash
# Tennis courts available tomorrow
uv run python main.py list --sport tennis --date tomorrow

# All available slots tomorrow
uv run python main.py list-available-slots --date tomorrow

# Specific location tomorrow
uv run python main.py list --location "Doral Central Park" --date tomorrow
```

## Sport-Specific Examples

### Tennis Players

```bash
# Find tennis courts
uv run python main.py list-courts --sport tennis

# Tennis locations
uv run python main.py list-locations --sport tennis

# Available tennis slots for the weekend
uv run python main.py list-available-slots --sport tennis --date +5
uv run python main.py list-available-slots --sport tennis --date +6

# Monitor tennis courts
uv run python main.py watch --sport tennis --interval 300
```

### Pickleball Players

```bash
# Pickleball court names
uv run python main.py list-courts --sport pickleball

# Pickleball locations with court counts
uv run python main.py list-locations --sport pickleball

# Available pickleball slots next week
uv run python main.py list-available-slots --sport pickleball --date +7

# Detailed pickleball time slots
uv run python main.py slots --sport pickleball --available-only
```

## Planning Examples

### Weekend Planning

```bash
# Check Friday availability
uv run python main.py list-available-slots --date +5

# Saturday morning slots
uv run python main.py slots --date +6 --available-only

# Sunday tennis
uv run python main.py list --sport tennis --date +7
```

### Event Planning

```bash
# Check specific date for tournament
uv run python main.py list-available-slots --date 08/15/2025 --sport tennis

# Get comprehensive data for analysis
uv run python main.py data --date 08/15/2025 --mode detailed --save-data

# Monitor leading up to event
uv run python main.py watch --date 08/15/2025 --interval 1800  # Check every 30 minutes
```

### Regular Playing Schedule

```bash
# Same time every week - check next Tuesday
uv run python main.py slots --date +7 --court "DCP Tennis Court 1"

# Monthly league planning
uv run python main.py list-available-slots --date +30 --sport pickleball
```

## Data Analysis Examples

### Current Conditions

```bash
# Comprehensive view of all data
uv run python main.py data --mode detailed

# Summary statistics
uv run python main.py data --mode summary

# Database statistics
uv run python main.py stats
```

### Historical Analysis

```bash
# What was available last week
uv run python main.py history --date -7 --mode summary

# Tennis availability trends
uv run python main.py history --sport tennis --mode detailed

# Compare availability over time
uv run python main.py history --date -30 --mode summary
uv run python main.py history --date -7 --mode summary
uv run python main.py data --mode summary
```

### Export for External Analysis

```bash
# Save data for spreadsheet analysis
uv run python main.py data --save-data --verbose

# Monitor and save data over time
uv run python main.py watch --save-data --interval 3600  # Every hour
```

## Location-Specific Examples

### Doral Central Park Focus

```bash
# All DCP courts
uv run python main.py list --location "Doral Central Park"

# DCP available slots
uv run python main.py list-available-slots --location "Doral Central Park"

# Monitor DCP tennis courts
uv run python main.py watch --sport tennis --location "Doral Central Park"
```

### Location Discovery

```bash
# Find all locations
uv run python main.py list-locations

# Locations with tennis courts
uv run python main.py list-locations --sport tennis

# Locations with pickleball courts
uv run python main.py list-locations --sport pickleball
```

## Monitoring Examples

### Real-time Monitoring

```bash
# Monitor all courts every 5 minutes
uv run python main.py watch

# Monitor tennis courts every 2 minutes
uv run python main.py watch --sport tennis --interval 120

# Monitor for tomorrow's availability
uv run python main.py watch --date tomorrow --interval 600
```

### Scheduled Monitoring

Create a shell script for automated monitoring:

```bash
#!/bin/bash
# monitor_courts.sh

# Check tennis courts every hour during business hours
while true; do
    hour=$(date +%H)
    if [ $hour -ge 8 ] && [ $hour -le 20 ]; then
        echo "$(date): Checking tennis courts..."
        uv run python main.py list-available-slots --sport tennis --date tomorrow >> tennis_log.txt
        sleep 3600  # 1 hour
    else
        sleep 1800  # 30 minutes during off hours
    fi
done
```

## Advanced Examples

### Batch Processing

```bash
# Check multiple dates
for days in 1 2 3 7 14; do
    echo "=== $days days from now ==="
    uv run python main.py list-available-slots --date +$days --sport tennis
    echo
done
```

### Conditional Logic

```bash
#!/bin/bash
# Check if tennis courts are available, if not check pickleball

tennis_count=$(uv run python main.py list-available-slots --sport tennis --date tomorrow | grep "Total Available" | grep -o '[0-9]\+' | head -1)

if [ "$tennis_count" -gt 0 ]; then
    echo "Tennis courts available for tomorrow: $tennis_count"
    uv run python main.py list-available-slots --sport tennis --date tomorrow
else
    echo "No tennis courts available, checking pickleball..."
    uv run python main.py list-available-slots --sport pickleball --date tomorrow
fi
```

### Data Pipeline

```bash
#!/bin/bash
# Daily data collection pipeline

date_str=$(date +%Y%m%d)

# Collect data
uv run python main.py data --save-data --mode detailed > "reports/daily_report_$date_str.txt"

# Get summary stats
uv run python main.py stats > "reports/stats_$date_str.txt"

# Check specific courts
uv run python main.py list-courts > "reports/courts_$date_str.txt"
uv run python main.py list-locations > "reports/locations_$date_str.txt"

echo "Daily report generated for $date_str"
```

## Troubleshooting Examples

### Network Issues

```bash
# Test with verbose logging
uv run python main.py list --verbose

# Test basic connectivity
uv run python main.py stats  # Uses local database only
```

### Data Issues

```bash
# Clear old data and fetch fresh
uv run python main.py cleanup --days 1
uv run python main.py list --verbose

# Check database content
uv run python main.py history --mode summary
```

### Debug Specific Court

```bash
# Get detailed info for one court
uv run python main.py slots --court "DCP Tennis Court 1" --verbose

# Check if court name exists
uv run python main.py list-courts | grep "Tennis Court 1"
```

## Integration Examples

### With Calendar Systems

```bash
# Export to calendar format (custom script)
uv run python main.py list-available-slots --date tomorrow | \
    python convert_to_calendar.py > tomorrow_slots.ics
```

### With Notification Systems

```bash
# Send notification when courts available (requires notification setup)
available=$(uv run python main.py list-available-slots --sport tennis --date tomorrow | grep "Total Available")
if [[ $available =~ [1-9] ]]; then
    notify-send "Tennis courts available tomorrow!"
fi
```

### With Web Services

```bash
# Post to webhook when monitoring detects changes
uv run python main.py watch --interval 300 | \
    python webhook_notifier.py --url "https://hooks.slack.com/..."
```

## Performance Examples

### Efficient Data Collection

```bash
# Use history command for historical data (faster)
uv run python main.py history --date yesterday

# Use fresh data only when needed
uv run python main.py list  # Always fresh
```

### Batch Operations

```bash
# Collect data for analysis period
for days_ago in {30..1}; do
    uv run python main.py history --date -$days_ago --mode summary >> analysis_data.txt
done
```

These examples cover most common use cases. Mix and match options to create workflows that fit your specific needs.
