# Doral Courts CLI - High-Value Feature Improvements

**Date**: 2025-10-31
**Current Version**: 0.1.0

This document proposes strategic feature improvements prioritized by value, feasibility, and user impact.

## Recent Updates

**2025-10-31**:

- ✅ **Feature #2 (Favorite Courts & Quick Access) - COMPLETED**
  - Implemented YAML-based configuration system
  - Added `favorites` command group (add/remove/list)
  - Added `query` command for saved query execution
  - Enhanced `list` command with `--favorites` flag
  - Star emoji (⭐) highlighting in all tables
  - Full documentation in README.md and reference.md

---

## Table of Contents

- [Priority Framework](#priority-framework)
- [High Priority (Quick Wins)](#high-priority-quick-wins)
- [Medium Priority (Major Features)](#medium-priority-major-features)
- [Low Priority (Future Vision)](#low-priority-future-vision)
- [Technical Debt & Infrastructure](#technical-debt--infrastructure)
- [Implementation Roadmap](#implementation-roadmap)

---

## Priority Framework

### Priority Levels

**🔴 HIGH (Quick Wins)**: High value, low effort, immediate impact

- Implementation: 1-5 days
- Dependencies: Minimal
- Risk: Low

**🟡 MEDIUM (Major Features)**: High value, moderate effort

- Implementation: 1-2 weeks
- Dependencies: Some
- Risk: Medium

**🟢 LOW (Future Vision)**: High value, high effort, long-term

- Implementation: 2+ weeks
- Dependencies: Many
- Risk: High

### Success Metrics

- **User Satisfaction**: Reduces friction, improves experience
- **Adoption**: Encourages more frequent usage
- **Reliability**: Reduces errors and failures
- **Extensibility**: Enables future features

---

## High Priority (Quick Wins)

### 1. 🔴 Smart Notifications & Alerts

**Problem**: Users must manually check availability; miss openings

**Solution**: Desktop/email notifications when courts become available

**Implementation**:

**Phase 1 - Desktop Notifications**:

```python
# New command: doral-courts notify
@click.command()
@click.option("--court", help="Court name to monitor")
@click.option("--sport", type=click.Choice(["tennis", "pickleball"]))
@click.option("--date", help="Date to monitor")
@click.option("--interval", default=300, help="Check interval in seconds")
def notify(court, sport, date, interval):
    """Monitor courts and send desktop notifications on availability"""
    # Use: plyer library for cross-platform notifications
    # or: notify-send (Linux), osascript (macOS), win10toast (Windows)
```

**Features**:

- Monitor specific court or all courts of a sport
- Desktop notification with sound when availability changes
- Configurable check interval (default: 5 minutes)
- Runs in background, logs to file

**Example**:

```bash
# Monitor tennis courts for tomorrow
doral-courts notify --sport tennis --date tomorrow --interval 300

# Notification:
# 🎾 Court Available!
# DLP Tennis Court 1 has 3 slots available for 11/01/2025
```

**Phase 2 - Email Notifications**:

```python
# Configuration file: ~/.doral-courts/config.yaml
notifications:
  email:
    enabled: true
    smtp_server: smtp.gmail.com
    smtp_port: 587
    from_email: user@gmail.com
    to_email: user@gmail.com
    app_password: <app_password>

  courts:
    - name: "DLP Tennis Court 1"
      sport: tennis
      dates: ["+1", "+2"]  # Tomorrow and day after
```

**Value**: ⭐⭐⭐⭐⭐ (Very High)

- Addresses primary user pain point
- Enables proactive booking
- Competitive advantage

**Effort**: 🔧 Low-Medium

- Desktop: 1-2 days (plyer library)
- Email: 2-3 days (smtplib + config)
- Total: 3-5 days

**Libraries**:

- `plyer` - Cross-platform notifications
- `smtplib` (built-in) - Email sending
- `pyyaml` - Configuration files

---

### 2. ✅ Favorite Courts & Quick Access (IMPLEMENTED)

**Status**: ✅ Completed (2025-10-31)

**Problem**: Users repeatedly type same court names/filters

**Solution**: Save favorite courts and common queries

**Implementation**:

**Configuration File** (`~/.doral-courts/config.yaml`):

```yaml
favorites:
  courts:
    - "DLP Tennis Court 1"
    - "DLP Tennis Court 2"

  queries:
    my_tennis:
      sport: tennis
      date: tomorrow
      status: available

    weekend_pickleball:
      sport: pickleball
      date: "+2"  # Day after tomorrow
      location: "Doral Central Park"

default_sport: tennis
default_date_offset: 1  # Default to tomorrow
```

**New Commands**:

```bash
# List favorites
doral-courts favorites list

# Add favorite court
doral-courts favorites add "DLP Tennis Court 3"

# Remove favorite
doral-courts favorites remove "DLP Tennis Court 1"

# Quick access to favorite courts
doral-courts list --favorites

# Run saved query
doral-courts query my_tennis
doral-courts query weekend_pickleball
```

**Features**:

- YAML config in user home directory
- Favorite courts highlighted in tables
- Saved queries with aliases
- Default preferences (sport, date offset)

**Value**: ⭐⭐⭐⭐ (High)

- Reduces repetitive typing
- Improves user experience
- Encourages daily usage

**Effort**: 🔧 Low

- 2-3 days implementation
- Uses standard library + pyyaml

**Implementation Details**:

- Created `src/doral_courts/utils/config.py` - YAML configuration management
- Created `src/doral_courts/cli/commands/favorites_cmd.py` - Favorites management (add/remove/list)
- Created `src/doral_courts/cli/commands/query_cmd.py` - Saved query execution
- Enhanced `src/doral_courts/cli/commands/list_cmd.py` - Added `--favorites` flag
- Enhanced `src/doral_courts/display/tables.py` - Star emoji (⭐) highlighting for favorites
- Configuration stored at `~/.doral-courts/config.yaml`
- Full documentation in README.md and reference.md

---

### 3. 🔴 Calendar View Export

**Problem**: Hard to visualize availability across multiple days

**Solution**: Export calendar view (text, HTML, iCal)

**Implementation**:

**Text Calendar View**:

```bash
doral-courts calendar --sport tennis --days 7

# Output:
╔════════════╦═══════╦═══════╦═══════╦═══════╦═══════╦═══════╦═══════╗
║ Court      ║ 11/01 ║ 11/02 ║ 11/03 ║ 11/04 ║ 11/05 ║ 11/06 ║ 11/07 ║
╠════════════╬═══════╬═══════╬═══════╬═══════╬═══════╬═══════╬═══════╣
║ Court 1    ║ 5/21  ║ 7/21  ║ 3/21  ║ 0/21  ║ 12/21 ║ 8/21  ║ 6/21  ║
║ Court 2    ║ 7/22  ║ 8/22  ║ 4/22  ║ 1/22  ║ 15/22 ║ 9/22  ║ 7/22  ║
╚════════════╩═══════╩═══════╩═══════╩═══════╩═══════╩═══════╩═══════╝

Legend: Available/Total slots
Green: >50% available | Yellow: 25-50% | Red: <25%
```

**HTML Export**:

```bash
doral-courts calendar --sport tennis --days 7 --format html --output calendar.html

# Creates interactive HTML calendar with hover details
```

**iCal Export** (for Google Calendar, Outlook):

```bash
doral-courts calendar --export ical --court "DLP Tennis Court 1" --days 7

# Creates: doral_courts_calendar.ics
# Import into calendar app for availability blocking
```

**Features**:

- Multi-day view (default: 7 days)
- Color-coded availability heatmap
- Export formats: text, HTML, iCal
- Filterable by sport, court, location

**Value**: ⭐⭐⭐⭐ (High)

- Visual planning for weekly schedules
- Integration with personal calendars
- Shareable HTML reports

**Effort**: 🔧 Low-Medium

- Text view: 2-3 days
- HTML export: 2-3 days
- iCal export: 1-2 days
- Total: 5-8 days

**Libraries**:

- `rich` (already used) - Text tables
- `jinja2` - HTML templating
- `icalendar` - iCal format generation

---

### 4. 🔴 Diff & Change Detection

**Problem**: Hard to spot what changed between checks

**Solution**: Show diffs between current and previous data

**Implementation**:

```bash
# Show what changed since last check
doral-courts diff --date tomorrow

# Output:
╔═══════════════════╦══════════╦════════════╗
║ Court             ║ Previous ║ Current    ║
╠═══════════════════╬══════════╬════════════╣
║ DLP Tennis Court 1║ 3/21 ✅  ║ 5/21 ⬆️    ║
║ DLP Tennis Court 2║ 7/22 ✅  ║ 4/22 ⬇️    ║
║ DLP Tennis Court 3║ 0/22 ❌  ║ 2/22 🆕    ║
╚═══════════════════╩══════════╩════════════╝

Legend: ⬆️ More available | ⬇️ Less available | 🆕 Now available | ❌ Fully booked
```

**Features**:

- Compare current vs. last fetch
- Compare any two dates in history
- Highlight newly available slots
- Show booking velocity (slots/hour)

**Advanced**: Change summary

```bash
doral-courts diff --summary

# Output:
Summary of changes in last 24 hours:
• 3 courts became fully available
• 5 courts lost >50% availability
• Peak booking time: 2pm-4pm
• Fastest booked: DLP Tennis Court 1 (21 slots → 0 in 3 hours)
```

**Value**: ⭐⭐⭐⭐ (High)

- Actionable insights on booking patterns
- Quick identification of opportunities
- Reduces cognitive load

**Effort**: 🔧 Low

- Basic diff: 2-3 days
- Summary analytics: 2-3 days
- Total: 4-6 days

---

### 5. 🔴 Smart Time Slot Recommendations

**Problem**: Users unsure which time slots are best

**Solution**: AI-powered recommendations based on history

**Implementation**:

```python
@click.command()
@click.option("--sport", required=True)
@click.option("--date", required=True)
@click.option("--duration", default=60, help="Desired duration in minutes")
def recommend(sport, date, duration):
    """Recommend best time slots based on historical availability"""

    # Algorithm:
    # 1. Query historical data for same day of week
    # 2. Calculate probability of availability by time slot
    # 3. Rank by: availability chance + preferred times (morning/evening)
    # 4. Show top 5 recommendations
```

**Output**:

```bash
doral-courts recommend --sport tennis --date tomorrow

# Output:
🎾 Top Time Slot Recommendations for Tennis on 11/01/2025

1. ⭐⭐⭐⭐⭐ 6:00 am - 7:00 am
   Availability: 95% (19/20 similar days had slots)
   Courts: DLP Court 1, 2, 3 typically available
   Notes: Best time for guaranteed availability

2. ⭐⭐⭐⭐ 7:00 am - 8:00 am
   Availability: 80% (16/20 similar days)
   Courts: DLP Court 1, 3
   Notes: Morning favorite, books quickly

3. ⭐⭐⭐ 6:00 pm - 7:00 pm
   Availability: 60% (12/20 similar days)
   Courts: DLP Court 2, 4
   Notes: Evening prime time, competitive

4. ⭐⭐ 9:00 am - 10:00 am
   Availability: 40% (8/20 similar days)
   Courts: DLP Court 5
   Notes: Mid-morning, less predictable

5. ⭐ 2:00 pm - 3:00 pm
   Availability: 20% (4/20 similar days)
   Courts: Rarely available
   Notes: Peak booking period, low chance
```

**Features**:

- Historical probability analysis
- Day-of-week patterns (Mondays vs Saturdays)
- Preferred time consideration (early morning, evening)
- Court-specific patterns
- Confidence scores

**Value**: ⭐⭐⭐⭐⭐ (Very High)

- Reduces decision fatigue
- Increases booking success rate
- Educational (learns patterns)

**Effort**: 🔧 Medium

- 5-7 days (statistical analysis + UI)
- Requires sufficient historical data

---

## Medium Priority (Major Features)

### 6. 🟡 Web Dashboard & API

**Problem**: CLI not accessible to all users; no remote access

**Solution**: Web interface with REST API

**Architecture**:

```
Frontend (Web Dashboard)
├── React/Vue.js SPA
├── Calendar view (FullCalendar.js)
├── Real-time updates (WebSocket)
└── Mobile-responsive

Backend (REST API)
├── FastAPI/Flask
├── JWT authentication
├── Rate limiting
├── WebSocket server
└── Background tasks (APScheduler)

Data Layer
├── SQLite (development)
├── PostgreSQL (production)
└── Redis cache
```

**API Endpoints**:

```
GET  /api/courts?sport=tennis&date=2025-11-01
GET  /api/courts/{id}
GET  /api/courts/{id}/slots
GET  /api/locations
GET  /api/stats
POST /api/notifications/subscribe
GET  /api/calendar?sport=tennis&days=7

WebSocket: /ws/updates
```

**Web Dashboard Features**:

- Interactive calendar with click-to-filter
- Real-time availability updates
- Save favorite courts
- Email notification management
- Historical trend charts
- Mobile-friendly responsive design

**Example URLs**:

```
https://doral-courts.app/
https://doral-courts.app/calendar?sport=tennis
https://doral-courts.app/courts/dlp-tennis-court-1
```

**Value**: ⭐⭐⭐⭐⭐ (Very High)

- Broader accessibility
- Mobile access
- Remote monitoring
- Shareable links

**Effort**: 🔧🔧 High

- API: 1-2 weeks
- Frontend: 2-3 weeks
- Deployment: 1 week
- Total: 4-6 weeks

**Tech Stack**:

- Backend: FastAPI (Python)
- Frontend: React + Vite
- Database: PostgreSQL
- Cache: Redis
- Hosting: Vercel (frontend), Railway (backend)

---

### 7. 🟡 Advanced Analytics & Insights

**Problem**: No visibility into booking patterns and trends

**Solution**: Comprehensive analytics dashboard

**Analytics Features**:

**1. Availability Trends**:

```bash
doral-courts analyze trends --sport tennis --days 30

# Output:
📊 Tennis Court Availability Trends (Last 30 Days)

Peak Booking Hours:
  1. 6pm-8pm: Average 15 slots booked/day
  2. 7am-9am: Average 12 slots booked/day
  3. 5pm-6pm: Average 10 slots booked/day

Day of Week Patterns:
  Monday:    ████████░░ 80% average availability
  Tuesday:   ██████████ 95% average availability  ⭐ Best day!
  Wednesday: ███████░░░ 70% average availability
  Thursday:  ██████░░░░ 65% average availability
  Friday:    ████░░░░░░ 45% average availability
  Saturday:  ███░░░░░░░ 35% average availability  ⚠️ Hardest day
  Sunday:    █████░░░░░ 50% average availability

Booking Velocity:
  Average time to full: 6.5 hours
  Fastest ever: 2.1 hours (DLP Court 1, Saturday 10/26)
```

**2. Prediction Model**:

```bash
doral-courts predict --sport tennis --date +7

# Output:
🔮 Availability Prediction for 11/08/2025 (Tuesday)

Based on 12 weeks of historical data:

DLP Tennis Court 1:
  Predicted availability: 18/21 slots (85%)  ⭐ Excellent
  Confidence: High (±2 slots)
  Best times: 6-8am (95%), 7-9pm (80%)

DLP Tennis Court 2:
  Predicted availability: 16/22 slots (72%)  ✅ Good
  Confidence: Medium (±3 slots)
  Best times: 6-7am (90%), 8-9pm (70%)

Recommendation: Book early morning for best selection.
Tuesday historically 25% less competitive than weekends.
```

**3. Court Comparison**:

```bash
doral-courts compare --courts "DLP Tennis Court 1" "DLP Tennis Court 2" --days 30

# Output:
⚖️ Court Comparison (Last 30 Days)

                       Court 1    Court 2    Advantage
────────────────────────────────────────────────────────
Avg Availability       78%        65%        Court 1 ⭐
Most Available Day     Tuesday    Monday     Varies
Peak Booking Time      6pm        5pm        Different
Price                  $0.00/hr   $0.00/hr   Tie
Capacity               3 players  3 players  Tie
Location               DCP        DCP        Tie

Summary: Court 1 is 13% more likely to have availability.
         Court 2 books earlier (5pm vs 6pm peak).
```

**4. Export Reports**:

```bash
# Generate PDF report
doral-courts report --sport tennis --days 30 --format pdf --output report.pdf

# Generate CSV for analysis
doral-courts export --format csv --days 90 --output courts_data.csv
```

**Value**: ⭐⭐⭐⭐ (High)

- Data-driven decision making
- Understanding of patterns
- Competitive intelligence

**Effort**: 🔧🔧 Medium-High

- Basic analytics: 1 week
- Prediction model: 1-2 weeks
- Reporting: 1 week
- Total: 3-4 weeks

**Libraries**:

- `pandas` - Data analysis
- `matplotlib`/`plotly` - Charts
- `scikit-learn` - ML predictions
- `reportlab` - PDF generation

---

### 8. 🟡 Multi-City & Court System Support

**Problem**: Hardcoded to Doral; not reusable

**Solution**: Configurable scrapers for multiple cities/systems

**Architecture**:

```python
# Abstract base scraper
class CourtSystemScraper(ABC):
    @abstractmethod
    def fetch_courts(self, date, sport):
        pass

    @abstractmethod
    def parse_response(self, html):
        pass

# City-specific implementations
class DoralScraper(CourtSystemScraper):
    base_url = "https://fldoralweb.myvscloud.com/..."
    # Doral-specific logic

class MiamiScraper(CourtSystemScraper):
    base_url = "https://miamidade.gov/..."
    # Miami-specific logic

class BrowardScraper(CourtSystemScraper):
    base_url = "https://broward.org/..."
    # Broward-specific logic
```

**Configuration**:

```yaml
# ~/.doral-courts/cities.yaml
cities:
  doral:
    name: Doral, FL
    scraper: DoralScraper
    base_url: https://fldoralweb.myvscloud.com/...
    enabled: true

  miami:
    name: Miami-Dade, FL
    scraper: MiamiScraper
    base_url: https://miamidade.gov/...
    enabled: false

  broward:
    name: Broward County, FL
    scraper: BrowardScraper
    base_url: https://broward.org/...
    enabled: false

default_city: doral
```

**Commands**:

```bash
# List supported cities
doral-courts cities list

# Switch active city
doral-courts config set city miami

# Multi-city query
doral-courts list --city doral --city miami --sport tennis
```

**Value**: ⭐⭐⭐⭐⭐ (Very High)

- Broad applicability
- Community contributions
- Network effects

**Effort**: 🔧🔧🔧 High

- Refactoring: 1-2 weeks
- New scrapers: 1 week per city
- Testing: 1 week
- Total: 3-4 weeks + ongoing

---

### 9. 🟡 Booking Integration (Read-Only → Write)

**Problem**: Can see availability but can't book

**Solution**: Automated booking capabilities

**⚠️ Legal/Ethical Considerations**:

- Respect terms of service
- Rate limiting essential
- May require official API partnership
- Consider liability

**Implementation** (if approved):

```bash
# Dry run (preview only)
doral-courts book --court "DLP Tennis Court 1" --date tomorrow --time "6:00 am" --dry-run

# Actual booking
doral-courts book --court "DLP Tennis Court 1" --date tomorrow --time "6:00 am" --confirm

# Auto-book when available
doral-courts auto-book --court "DLP Tennis Court 1" --date tomorrow --time "6:00 am" --monitor
```

**Features**:

- Account credentials management (secure storage)
- Two-factor authentication support
- Booking confirmation emails
- Automatic retry on failure
- Calendar integration (add to Google Calendar)
- Cancellation support

**Safety Features**:

- Dry-run mode (preview before booking)
- Confirmation prompts
- Rate limiting (respect website)
- Booking logs and audit trail
- Failure notifications

**Value**: ⭐⭐⭐⭐⭐ (Very High) - If allowed

- End-to-end solution
- Competitive advantage
- User lock-in

**Effort**: 🔧🔧🔧 High

- 3-4 weeks development
- Legal review required
- High risk of breakage

**Risks**: 🚨 HIGH

- Terms of service violation
- Account bans
- Legal liability
- Website changes break integration

**Recommendation**: Pursue only with official partnership or explicit permission

---

## Low Priority (Future Vision)

### 10. 🟢 Mobile Apps (iOS/Android)

**Solution**: Native mobile applications

**Features**:

- Push notifications (more reliable than desktop)
- Location-based court finder
- Quick booking from notifications
- Calendar integration
- Offline mode (historical data)

**Tech Stack**:

- React Native (cross-platform)
- Or: Flutter
- Or: SwiftUI + Kotlin (native)

**Value**: ⭐⭐⭐⭐⭐ (Very High)
**Effort**: 🔧🔧🔧🔧 Very High (8-12 weeks)

---

### 11. 🟢 Social Features

**Solution**: Community-driven enhancements

**Features**:

- User reviews of courts (surface quality, lighting, etc.)
- Court photos gallery
- Availability reports from users
- Player matching (find partners)
- Group bookings coordination
- League/tournament organization

**Value**: ⭐⭐⭐⭐ (High)
**Effort**: 🔧🔧🔧🔧 Very High (12+ weeks)

---

### 12. 🟢 AI Chatbot Interface

**Solution**: Conversational AI for natural queries

**Implementation**:

```bash
doral-courts chat

> "Show me tennis courts available tomorrow morning"
> "When is Court 1 usually free on Mondays?"
> "Notify me when any court opens up for this Saturday"
```

**Tech**: OpenAI API, LangChain, vector embeddings

**Value**: ⭐⭐⭐⭐ (High)
**Effort**: 🔧🔧🔧 High (4-6 weeks)

---

## Technical Debt & Infrastructure

### 13. Testing & Quality

**Current State**: Limited test coverage (HTML extractor only)

**Improvements**:

1. **Expand Unit Tests**:
   - Database operations
   - Date parsing edge cases
   - Display formatting
   - Filter logic

2. **Integration Tests**:
   - End-to-end command flows
   - Database migrations
   - File exports

3. **Mock Web Scraping**:
   - Use `responses` library
   - Cached HTML fixtures
   - Simulate Cloudflare challenges

4. **CI/CD Pipeline**:
   - GitHub Actions
   - Automated testing on PRs
   - Coverage reporting (Codecov)
   - Linting/formatting checks

**Effort**: 🔧🔧 Medium (1-2 weeks)

---

### 14. Error Handling & Reliability

**Improvements**:

1. **Retry Logic**:

   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
   def fetch_with_retry(url):
       # Automatic retry with exponential backoff
   ```

2. **Circuit Breaker**:
   - Stop hammering failing website
   - Fallback to cached data
   - Auto-recovery after cooldown

3. **Health Checks**:

   ```bash
   doral-courts health
   # ✅ Database: OK (1234 records)
   # ✅ Website: OK (response time: 1.2s)
   # ⚠️ Cloudflare: Slow (challenge solved in 8.5s)
   ```

4. **Better Error Messages**:
   - Actionable suggestions
   - Debug information links
   - Common problem solutions

**Effort**: 🔧 Low-Medium (3-5 days)

---

### 15. Performance Optimization

**Improvements**:

1. **Caching Layer**:

   ```python
   from functools import lru_cache
   from cachetools import TTLCache

   # Cache parsed data for 5 minutes
   @lru_cache(maxsize=100)
   def get_courts_cached(date, sport):
       # Reduce redundant fetches
   ```

2. **Async Operations**:

   ```python
   import asyncio
   import aiohttp

   # Parallel fetching for multi-day queries
   async def fetch_multiple_dates(dates):
       tasks = [fetch_date(d) for d in dates]
       return await asyncio.gather(*tasks)
   ```

3. **Database Optimization**:
   - Add compound indexes
   - Query optimization
   - Connection pooling

4. **Lazy Loading**:
   - Stream large results
   - Paginate table displays

**Effort**: 🔧🔧 Medium (1 week)

---

### 16. Documentation

**Improvements**:

1. **User Guide**:
   - Detailed tutorials
   - Video walkthroughs
   - FAQ section

2. **API Documentation**:
   - Function docstrings
   - Type hints everywhere
   - Architecture diagrams

3. **Contributing Guide**:
   - Developer setup
   - Code style guide
   - PR templates

4. **Man Pages**:

   ```bash
   man doral-courts
   man doral-courts-list
   ```

**Effort**: 🔧 Low (ongoing)

---

## Implementation Roadmap

### Phase 1: Quick Wins (Weeks 1-3)

**Week 1**:

- ⏳ Smart Notifications (desktop) - Not started
- ✅ Favorites & Quick Access - **COMPLETED 2025-10-31**

**Week 2**:

- ⏳ Calendar View Export - Not started
- ⏳ Diff & Change Detection - Not started

**Week 3**:

- ⏳ Smart Recommendations - Not started
- ⏳ Testing improvements - Not started

**Deliverables**: 5 new features, 90% test coverage
**Progress**: 1/5 features completed (20%)

---

### Phase 2: Major Features (Weeks 4-9)

**Weeks 4-6**:

- 🌐 Web Dashboard & API
  - Week 4: API backend
  - Week 5: Frontend development
  - Week 6: Integration & deployment

**Weeks 7-9**:

- 📊 Advanced Analytics
- 🌍 Multi-City Support

**Deliverables**: Web app, API, analytics dashboard

---

### Phase 3: Future Vision (Weeks 10+)

**Weeks 10-12**:

- 📱 Mobile Apps (React Native)

**Weeks 13-15**:

- 👥 Social Features
- 🤖 AI Chatbot

**Deliverables**: Mobile apps, community features

---

## Prioritization Matrix

| Feature         | Value | Effort      | Priority | Timeline  | Status     |
| --------------- | ----- | ----------- | -------- | --------- | ---------- |
| Notifications   | ⭐⭐⭐⭐⭐ | 🔧 Low       | 🔴 HIGH   | Week 1    | ⏳ Pending  |
| Favorites       | ⭐⭐⭐⭐  | 🔧 Low       | 🔴 HIGH   | Week 1    | ✅ Complete |
| Calendar View   | ⭐⭐⭐⭐  | 🔧 Low-Med   | 🔴 HIGH   | Week 2    | ⏳ Pending  |
| Diff Detection  | ⭐⭐⭐⭐  | 🔧 Low       | 🔴 HIGH   | Week 2    | ⏳ Pending  |
| Recommendations | ⭐⭐⭐⭐⭐ | 🔧 Med       | 🔴 HIGH   | Week 3    | ⏳ Pending  |
| Web Dashboard   | ⭐⭐⭐⭐⭐ | 🔧🔧 High     | 🟡 MED    | Weeks 4-6 |
| Analytics       | ⭐⭐⭐⭐  | 🔧🔧 Med-High | 🟡 MED    | Weeks 7-8 |
| Multi-City      | ⭐⭐⭐⭐⭐ | 🔧🔧🔧 High    | 🟡 MED    | Week 9    |
| Booking         | ⭐⭐⭐⭐⭐ | 🔧🔧🔧 High    | ⚠️ RISK   | TBD       |
| Mobile Apps     | ⭐⭐⭐⭐⭐ | 🔧🔧🔧🔧 V.High | 🟢 LOW    | Weeks 10+ |
| Social Features | ⭐⭐⭐⭐  | 🔧🔧🔧🔧 V.High | 🟢 LOW    | Weeks 13+ |
| AI Chatbot      | ⭐⭐⭐⭐  | 🔧🔧🔧 High    | 🟢 LOW    | Future    |

---

## Success Metrics

### User Adoption

- **Target**: 100 daily active users by Month 3
- **Measure**: Daily command executions, unique IPs (web)

### Engagement

- **Target**: 5 commands/user/day average
- **Measure**: Command frequency, feature usage

### Reliability

- **Target**: 99% uptime, <5% error rate
- **Measure**: Health checks, error logs

### Growth

- **Target**: 20% MoM user growth
- **Measure**: New users, retention rate

---

## Risk Assessment

### High Risk

- ⚠️ **Booking Integration**: ToS violation, legal issues
- ⚠️ **Website Changes**: HTML structure breaks scraper
- ⚠️ **Cloudflare Updates**: Bypass stops working

**Mitigation**:

- Monitor website changes via alerts
- Maintain HTML fixtures for quick testing
- Build parser flexibility with fallbacks
- Legal review before booking features

### Medium Risk

- ⚠️ **Performance**: Slow under load
- ⚠️ **Data Quality**: Inaccurate parsing

**Mitigation**:

- Load testing, caching, async operations
- Extensive test coverage, validation

### Low Risk

- Feature adoption slow
- UI/UX issues

**Mitigation**:

- User feedback loops
- A/B testing, analytics

---

## Conclusion

This roadmap prioritizes **Quick Wins** (notifications, favorites, calendar) for immediate user value, followed by **Major Features** (web dashboard, analytics) for scale, and **Future Vision** (mobile, social) for long-term growth.

**Recommended First Steps**:

1. ⏳ Implement desktop notifications (Week 1) - Pending
2. ✅ Add favorites system (Week 1) - **COMPLETED 2025-10-31**
3. ⏳ Build calendar export (Week 2) - Pending
4. ⏳ Create diff detection (Week 2) - Pending
5. ⏳ Launch smart recommendations (Week 3) - Pending

This approach delivers tangible value quickly while building toward a comprehensive court availability platform.

**Next Actions**:

- [x] ✅ Add favorites system - **COMPLETED 2025-10-31**
- [ ] User survey to validate priorities
- [ ] Prototype notifications for feedback
- [ ] Set up analytics tracking
- [ ] Create GitHub project board
- [ ] Continue implementation with Feature #1 (Smart Notifications) or Feature #3 (Calendar View)

---

**Questions? Feedback?**

- GitHub Issues: <https://github.com/yorch/doral-courts/issues>
- Discussions: <https://github.com/yorch/doral-courts/discussions>
