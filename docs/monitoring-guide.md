# Court Monitoring & Booking Analytics Guide

This guide explains how to use the continuous monitoring and analytics features to track court booking patterns and answer questions like: *"How long does it take for a pickleball court to get booked for 8am on Fridays?"*

## Table of Contents

- [Overview](#overview)
  - [Database Configuration](#database-configuration)
- [Quick Start](#quick-start)
- [Use Cases](#use-cases)
- [Monitor Command](#monitor-command)
- [Analyze Command](#analyze-command)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

The monitoring and analytics features work together to help you understand court booking patterns:

1. **`monitor`** - Continuously polls the court reservation system and stores historical data
2. **`analyze`** - Analyzes the collected data to reveal booking velocity and availability patterns

### How It Works

**The 24-Hour Rule**: Doral courts can only be reserved 24 hours in advance. For example:

- To book a court for Friday 8:00am, reservations open Thursday 8:00am
- The court transitions from "not yet available" → "available" → "booked"

**What We Track**:

- When courts become available (24 hours before)
- When courts get booked (transition from available → unavailable)
- Time difference = **booking velocity** (how fast courts get reserved)

### Database Storage

All monitoring data is automatically stored in `doral_courts.db`:

- **Courts Table**: 184+ aggregated court records
- **Time Slots Table**: 17,620+ individual time slot records with timestamps
- **Tracking**: Every poll saves the current state with timestamp
- **Deduplication**: Only changed data is stored to save space

### Database Configuration

By default, the CLI uses SQLite (a local file database). For larger deployments or production use, you can configure PostgreSQL.

**SQLite (Default)**:

- Local file-based database (`doral_courts.db`)
- No setup required
- Perfect for personal use
- Easy to backup (just copy the file)

**PostgreSQL (Optional)**:

- Client-server database
- Better performance for high-frequency monitoring
- Concurrent access support
- Suitable for production deployments

#### Configuring PostgreSQL

1. **Install PostgreSQL Support**:

```bash
# Install with PostgreSQL support
uv pip install doral-courts[postgresql]

# Or add to existing installation
uv pip install psycopg2-binary
```

2. **Create PostgreSQL Database**:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE doral_courts;

# Create user (optional)
CREATE USER doral_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE doral_courts TO doral_user;
\q
```

3. **Configure in `~/.doral-courts/config.yaml`**:

```yaml
database:
  type: postgresql  # Change from 'sqlite' to 'postgresql'
  postgresql:
    host: localhost
    port: 5432
    database: doral_courts
    user: doral_user
    password: your_password
  # sqlite:  # No longer used when type is postgresql
  #   path: doral_courts.db
```

4. **Verify Configuration**:

```bash
# Test database connection
uv run doral-courts stats

# You should see PostgreSQL in the logs
# "Creating PostgreSQL adapter for doral_user@localhost:5432/doral_courts"
```

**When to Use PostgreSQL**:

- High-frequency monitoring (intervals < 5 minutes)
- Multiple concurrent monitors
- Production deployments
- Server environments
- Need for database backups/replication

**Switching Between Databases**:

```yaml
# Switch back to SQLite
database:
  type: sqlite
  sqlite:
    path: doral_courts.db
```

Note: Data is not automatically migrated between SQLite and PostgreSQL. If switching, you'll start with an empty database.

---

## Quick Start

### 1. Start Monitoring (Background)

Run the monitor in the background to collect data continuously:

```bash
# Basic monitoring (all courts, every 10 minutes)
nohup uv run doral-courts monitor --quiet > monitor.log 2>&1 &

# Targeted monitoring (pickleball only, every 5 minutes)
nohup uv run doral-courts monitor --sport pickleball --interval 5 --quiet > monitor.log 2>&1 &

# Check it's running
tail -f monitor.log
```

### 2. Let It Collect Data

**Minimum**: 3-7 days for initial patterns
**Recommended**: 2-4 weeks for reliable statistics
**Best**: Ongoing monitoring for trend analysis

### 3. Analyze the Data

After collecting data, run analysis queries:

```bash
# How fast do pickleball courts get booked?
uv run doral-courts analyze --sport pickleball --mode velocity

# Which days have best availability?
uv run doral-courts analyze --sport tennis --mode availability

# Comprehensive analysis
uv run doral-courts analyze --mode summary
```

### 4. Stop Monitoring

```bash
# Find the process ID
ps aux | grep "doral-courts monitor"

# Stop gracefully
kill <PID>

# Or stop immediately (not recommended)
kill -9 <PID>
```

---

## Use Cases

### Use Case 1: Friday Morning Pickleball Booking Window

**Question**: *"How long does it take for DLP pickleball courts to get booked for 8:00am on Fridays?"*

**Setup**:

```bash
# Start targeted monitoring
nohup uv run doral-courts monitor \
  --sport pickleball \
  --interval 5 \
  --days-ahead 2 \
  --quiet > pickleball_monitor.log 2>&1 &
```

**After 2-3 weeks, analyze**:

```bash
# Specific analysis for Friday 8am at DLP
uv run doral-courts analyze \
  --sport pickleball \
  --location "Doral Legacy Park" \
  --time-slot "8:00 am" \
  --day-of-week Friday \
  --mode velocity
```

**Expected Output**:

```
📊 Court Booking Analysis
Period: 2025-07-03 to 2025-10-31
Scope: Pickleball at Doral Legacy Park on Fridays at 8:00 am

🚀 Booking Velocity Analysis

Found 12 booking transitions

⏱️  Average booking time: 45.3 minutes
⚡ Fastest booking: 2.0 minutes
   DLP Pickleball Court 4A on 10/18/2025 at 8:00 am
🐌 Slowest booking: 245.0 minutes
   DLP Pickleball Court 5B on 10/04/2025 at 8:00 am

⚡ Top 10 Fastest Bookings:
Court                   Date       Time     Minutes  Day
DLP Pickleball Court 4A 10/18/2025 8:00 am  2m      Friday
DLP Pickleball Court 4B 10/18/2025 8:00 am  5m      Friday
...
```

**Interpretation**:

- Most Friday 8am slots book within 45 minutes of becoming available
- The fastest slot booked in just 2 minutes (very competitive!)
- You need to be ready when reservations open on Thursday 8am

---

### Use Case 2: Finding the Best Booking Day

**Question**: *"Which day of the week has the best tennis court availability?"*

**Setup**:

```bash
# Monitor tennis courts
nohup uv run doral-courts monitor \
  --sport tennis \
  --interval 10 \
  --quiet > tennis_monitor.log 2>&1 &
```

**Analyze**:

```bash
# Availability patterns by day
uv run doral-courts analyze \
  --sport tennis \
  --mode availability \
  --days 30
```

**Expected Output**:

```
📅 Availability Patterns

📊 Availability by Day of Week:
Day       Available  Fully Booked  Availability %
Monday          45            5          90.0%  ⭐ Best day!
Tuesday         42            8          84.0%
Wednesday       38           12          76.0%
Thursday        35           15          70.0%
Friday          25           25          50.0%
Saturday        15           35          30.0%
Sunday          20           30          40.0%  ⚠️ Competitive
```

**Interpretation**:

- Monday and Tuesday are the best days to find available courts
- Weekends (Saturday/Sunday) are most competitive
- Friday availability drops significantly

---

### Use Case 3: Evening vs. Morning Booking Patterns

**Question**: *"Are morning or evening slots more competitive?"*

**Analyze Morning Slots**:

```bash
uv run doral-courts analyze \
  --sport tennis \
  --time-slot "8:00 am" \
  --mode velocity \
  --days 30
```

**Analyze Evening Slots**:

```bash
uv run doral-courts analyze \
  --sport tennis \
  --time-slot "6:00 pm" \
  --mode velocity \
  --days 30
```

**Compare Results**:

- Average booking time for 8:00am slots: 125 minutes
- Average booking time for 6:00pm slots: 35 minutes
- **Conclusion**: Evening slots are 3.5x more competitive!

---

## Monitor Command

### Command Syntax

```bash
doral-courts monitor [OPTIONS]
```

### Options

| Option         | Description                                    | Default |
| -------------- | ---------------------------------------------- | ------- |
| `--interval`   | Polling interval in minutes                    | 10      |
| `--sport`      | Filter by sport (tennis/pickleball)            | both    |
| `--location`   | Filter by location (e.g., "Doral Legacy Park") | all     |
| `--days-ahead` | Number of days to monitor ahead                | 2       |
| `--quiet`      | Suppress console output (logs only)            | false   |

### Examples

```bash
# Basic monitoring - all courts every 10 minutes
uv run doral-courts monitor

# Pickleball only, check every 5 minutes
uv run doral-courts monitor --sport pickleball --interval 5

# Monitor specific location, next 3 days, quietly
uv run doral-courts monitor \
  --location "Doral Central Park" \
  --days-ahead 3 \
  --quiet

# Aggressive monitoring (every 2 minutes)
uv run doral-courts monitor --interval 2
```

### Monitoring Best Practices

**Interval Selection**:

- **2-5 minutes**: Aggressive (use for critical slots like Friday mornings)
- **10 minutes**: Balanced (default, good for general monitoring)
- **15-30 minutes**: Conservative (less load on website, still useful data)

**Resource Considerations**:

- Each poll fetches data for all specified days
- Use `--quiet` for background operation
- Monitor logs grow ~1KB per poll (plan disk space accordingly)
- Database grows ~100-200 bytes per court per poll

**Running in Background**:

```bash
# Using nohup (survives terminal close)
nohup uv run doral-courts monitor --quiet > monitor.log 2>&1 &

# Using screen (can reattach later)
screen -S monitor
uv run doral-courts monitor
# Press Ctrl+A, then D to detach

# Using systemd (for servers)
# See section below for systemd service setup
```

### Systemd Service (Linux Servers)

Create `/etc/systemd/system/doral-courts-monitor.service`:

```ini
[Unit]
Description=Doral Courts Monitoring Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/doral-courts
ExecStart=/usr/bin/uv run doral-courts monitor --quiet
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable doral-courts-monitor
sudo systemctl start doral-courts-monitor
sudo systemctl status doral-courts-monitor
```

---

## Analyze Command

### Command Syntax

```bash
doral-courts analyze [OPTIONS]
```

### Options

| Option          | Description                                   | Default |
| --------------- | --------------------------------------------- | ------- |
| `--sport`       | Filter by sport (tennis/pickleball)           | all     |
| `--location`    | Filter by location                            | all     |
| `--court`       | Filter by specific court name                 | all     |
| `--time-slot`   | Filter by time slot (e.g., "8:00 am")         | all     |
| `--day-of-week` | Filter by day (Monday-Sunday)                 | all     |
| `--days`        | Number of days of history to analyze          | 30      |
| `--mode`        | Analysis mode (velocity/availability/summary) | summary |

### Analysis Modes

**1. Velocity Mode** (`--mode velocity`):

- Shows how quickly courts transition from available to booked
- Identifies fastest and slowest booking times
- Top 10 fastest bookings table
- Average booking time statistics

**2. Availability Mode** (`--mode availability`):

- Day-of-week availability patterns
- Percentage of available vs. fully booked courts
- Best and worst days for booking

**3. Summary Mode** (`--mode summary`):

- Combines both velocity and availability analysis
- Comprehensive overview of booking patterns

### Examples

```bash
# Quick velocity check for pickleball
uv run doral-courts analyze --sport pickleball --mode velocity

# Deep dive on specific court
uv run doral-courts analyze \
  --court "DLP Tennis Court 1" \
  --days 60 \
  --mode summary

# Find best day for tennis
uv run doral-courts analyze \
  --sport tennis \
  --mode availability

# Friday morning pickleball patterns
uv run doral-courts analyze \
  --sport pickleball \
  --day-of-week Friday \
  --time-slot "8:00 am" \
  --mode velocity

# Compare locations
uv run doral-courts analyze --location "Doral Legacy Park"
uv run doral-courts analyze --location "Doral Central Park"
```

### Understanding the Output

**Booking Velocity Metrics**:

```
⏱️  Average booking time: 690.0 minutes
```

- How long courts typically stay available after opening
- Lower = more competitive
- Higher = easier to book

```
⚡ Fastest booking: 0.0 minutes
```

- Shortest time from available → booked
- 0 minutes = instant booking (extremely competitive)
- Helps identify "must book immediately" slots

```
🐌 Slowest booking: 1072.0 minutes
```

- Longest time a slot stayed available
- Indicates less popular times
- Good targets for casual booking

**Availability Percentages**:

```
Saturday: 13.6% available
```

- Only 13.6% of Saturday slots remain available (competitive!)
- 86.4% get fully booked

```
Monday: 100.0% available
```

- All Monday slots typically available (easy booking)

---

## Best Practices

### Data Collection Strategy

**Phase 1: Initial Collection (Week 1-2)**

- Start with broad monitoring (all courts, all sports)
- Interval: 10-15 minutes
- Goal: Build baseline data

**Phase 2: Targeted Monitoring (Week 3+)**

- Focus on specific courts/times of interest
- Reduce interval to 5 minutes for competitive slots
- Goal: Detailed velocity data for key booking windows

**Phase 3: Maintenance Monitoring (Ongoing)**

- Continue monitoring at 15-30 minute intervals
- Focus on specific sports or locations
- Goal: Track trends and seasonal changes

### Query Patterns

**Start Broad, Then Narrow**:

```bash
# 1. Overview
uv run doral-courts analyze --mode summary

# 2. Identify sport patterns
uv run doral-courts analyze --sport pickleball --mode availability

# 3. Focus on specific day
uv run doral-courts analyze --sport pickleball --day-of-week Friday

# 4. Drill into specific time
uv run doral-courts analyze \
  --sport pickleball \
  --day-of-week Friday \
  --time-slot "8:00 am" \
  --mode velocity
```

### Data Maintenance

**Check Database Size**:

```bash
# View database stats
uv run doral-courts stats

# Check actual file size
ls -lh doral_courts.db
```

**Clean Old Data** (if needed):

```bash
# Remove data older than 90 days
uv run doral-courts cleanup --days 90

# Check what would be deleted (dry run)
sqlite3 doral_courts.db "SELECT COUNT(*) FROM courts WHERE date < date('now', '-90 days')"
```

---

## Troubleshooting

### Monitor Not Collecting Data

**Check Process Status**:

```bash
# Find monitor process
ps aux | grep "doral-courts monitor"

# Check logs
tail -f monitor.log
```

**Common Issues**:

1. **"No courts retrieved"**
   - Website may be blocking requests (too frequent polling)
   - Solution: Increase `--interval` to 15-30 minutes
   - Check if website is accessible: `curl https://fldoralweb.myvscloud.com/...`

2. **Process died unexpectedly**
   - Check logs for error messages
   - Ensure enough disk space for database
   - Check memory usage: `free -h`

3. **Database locked errors**
   - Multiple processes accessing database simultaneously
   - Solution: Stop duplicate monitors, only run one instance

### Analyze Shows No Data

**Verify Data Exists**:

```bash
# Check time slots count
uv run doral-courts stats

# View database directly
python scripts/view_db.py
```

**Common Issues**:

1. **"No time slot data available"**
   - Monitor hasn't run long enough
   - Need at least 2 polls to calculate velocity (available → unavailable transition)
   - Solution: Wait for more data collection

2. **"No booking velocity data found"**
   - Filters too restrictive (no matching data)
   - Time range too narrow
   - Solution: Broaden filters or increase `--days`

3. **Data too old**
   - Analysis defaults to last 30 days
   - Your data might be older
   - Solution: Increase `--days 60` or `--days 90`

### Performance Issues

**Slow Queries**:

```bash
# Check database size
ls -lh doral_courts.db

# If > 100MB, consider cleanup
uv run doral-courts cleanup --days 60
```

**High CPU/Memory**:

- Reduce monitoring interval
- Use `--quiet` flag to reduce output processing
- Monitor specific sport/location instead of all courts

---

## Advanced Usage

### Comparing Multiple Scenarios

Create a shell script to compare different patterns:

```bash
#!/bin/bash
# compare_courts.sh

echo "=== DLP Friday 8am ==="
uv run doral-courts analyze \
  --location "Doral Legacy Park" \
  --day-of-week Friday \
  --time-slot "8:00 am" \
  --mode velocity

echo "\n=== DLP Saturday 8am ==="
uv run doral-courts analyze \
  --location "Doral Legacy Park" \
  --day-of-week Saturday \
  --time-slot "8:00 am" \
  --mode velocity

echo "\n=== DCP Friday 8am ==="
uv run doral-courts analyze \
  --location "Doral Central Park" \
  --day-of-week Friday \
  --time-slot "8:00 am" \
  --mode velocity
```

### Exporting Analysis Results

Export to CSV for further analysis:

```bash
# Direct SQL query
sqlite3 -csv doral_courts.db \
  "SELECT * FROM time_slots WHERE date > date('now', '-30 days')" \
  > booking_data.csv

# Open in spreadsheet for custom analysis
```

### Alerting on Patterns

Monitor for specific conditions and send alerts:

```bash
#!/bin/bash
# alert_on_availability.sh

RESULT=$(uv run doral-courts analyze \
  --sport pickleball \
  --day-of-week Friday \
  --mode velocity \
  | grep "Average booking time")

# If booking time < 30 minutes, send alert
if [[ $RESULT =~ ([0-9]+\.?[0-9]*) ]]; then
  MINUTES="${BASH_REMATCH[1]}"
  if (( $(echo "$MINUTES < 30" | bc -l) )); then
    # Send notification (mail, SMS, Slack, etc.)
    echo "Alert: Friday slots book in $MINUTES minutes!" | mail -s "Court Alert" you@email.com
  fi
fi
```

---

## Next Steps

1. **Start Monitoring**: Begin collecting data with `monitor` command
2. **Wait Patiently**: Let it run for 2-4 weeks for reliable patterns
3. **Analyze Regularly**: Run weekly analysis to track trends
4. **Optimize Booking**: Use insights to book at optimal times

**Pro Tip**: The longer you monitor, the better your predictions become. Seasonal patterns may emerge over months!

---

## Related Documentation

- [Reference Guide](./reference.md) - Complete command documentation
- [Feature Improvements](./feature-improvements.md) - Planned enhancements
- [Examples](./examples.md) - More usage examples

---

**Questions or Issues?**

- GitHub Issues: <https://github.com/yorch/doral-courts/issues>
- Documentation: <https://github.com/yorch/doral-courts/docs>
