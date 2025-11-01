"""Analyze command for booking velocity and pattern analysis."""

import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from ...core.database import Database
from ...utils.logger import get_logger

logger = get_logger(__name__)
console = Console()


@click.command()
@click.option(
    "--sport",
    type=click.Choice(["tennis", "pickleball"], case_sensitive=False),
    help="Filter by sport type",
)
@click.option(
    "--location",
    help="Filter by location (e.g., 'Doral Legacy Park', 'Doral Central Park')",
)
@click.option(
    "--court",
    help="Filter by specific court name",
)
@click.option(
    "--time-slot",
    help="Filter by time slot (e.g., '8:00 am', '6:00 pm')",
)
@click.option(
    "--day-of-week",
    type=click.Choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], case_sensitive=False),
    help="Filter by day of week",
)
@click.option(
    "--days",
    default=30,
    help="Number of days of history to analyze (default: 30)",
    type=int,
)
@click.option(
    "--mode",
    type=click.Choice(["velocity", "availability", "summary"], case_sensitive=False),
    default="summary",
    help="Analysis mode: velocity (booking speed), availability (patterns), summary (both)",
)
def analyze(
    sport: Optional[str],
    location: Optional[str],
    court: Optional[str],
    time_slot: Optional[str],
    day_of_week: Optional[str],
    days: int,
    mode: str,
):
    """Analyze court booking patterns and velocity.

    This command analyzes historical data to understand booking patterns:
    - How quickly courts get fully booked after becoming available
    - Which days/times are most competitive
    - Availability trends and patterns

    Examples:
        # Analyze pickleball booking velocity
        doral-courts analyze --sport pickleball --mode velocity

        # See Friday 8am patterns for DLP
        doral-courts analyze --location "Doral Legacy Park" --time-slot "8:00 am" --day-of-week Friday

        # Full summary for specific court
        doral-courts analyze --court "DLP Tennis Court 1" --mode summary

        # Availability patterns for last 60 days
        doral-courts analyze --sport tennis --days 60 --mode availability
    """
    db = Database()

    # Build filters
    filters = []
    if sport:
        filters.append(f"sport_type = '{sport.title()}'")
    if location:
        filters.append(f"location LIKE '%{location}%'")
    if court:
        filters.append(f"name = '{court}'")

    filter_clause = " AND ".join(filters) if filters else "1=1"

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Build description
    desc_parts = []
    if sport:
        desc_parts.append(sport.title())
    if location:
        desc_parts.append(f"at {location}")
    if court:
        desc_parts.append(f"({court})")
    if day_of_week:
        desc_parts.append(f"on {day_of_week}s")
    if time_slot:
        desc_parts.append(f"at {time_slot}")

    description = " ".join(desc_parts) if desc_parts else "All courts"

    console.print(f"\n[bold]📊 Court Booking Analysis[/bold]")
    console.print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    console.print(f"Scope: {description}\n")

    if mode in ["velocity", "summary"]:
        _analyze_booking_velocity(
            db, filter_clause, start_date, end_date, time_slot, day_of_week
        )

    if mode in ["availability", "summary"]:
        _analyze_availability_patterns(
            db, filter_clause, start_date, end_date, day_of_week
        )


def _analyze_booking_velocity(
    db: Database,
    filter_clause: str,
    start_date: datetime,
    end_date: datetime,
    time_slot_filter: Optional[str],
    day_of_week_filter: Optional[str],
):
    """Analyze how quickly courts get booked after becoming available."""

    console.print("[bold cyan]🚀 Booking Velocity Analysis[/bold cyan]\n")

    # Query time slots data with court info
    query = f"""
        SELECT
            c.name,
            c.location,
            c.sport_type,
            ts.date,
            ts.start_time,
            ts.status,
            ts.last_updated
        FROM time_slots ts
        JOIN courts c ON ts.court_id = c.id
        WHERE {filter_clause}
        AND ts.date BETWEEN ? AND ?
        ORDER BY c.name, ts.date, ts.start_time, ts.last_updated
    """

    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute(query, (start_date.strftime("%m/%d/%Y"), end_date.strftime("%m/%d/%Y")))
    rows = cursor.fetchall()

    if not rows:
        console.print("[yellow]No time slot data available for analysis.[/yellow]")
        console.print("[dim]💡 Run 'doral-courts monitor' to collect historical data[/dim]\n")
        return

    # Track booking transitions: Available → Unavailable
    # Group by (court, date, time_slot)
    booking_events = defaultdict(list)

    for row in rows:
        court_name, location, sport, date, start_time, status, last_updated = row

        # Apply filters
        if time_slot_filter and start_time != time_slot_filter:
            continue

        # Parse date and check day of week
        try:
            date_obj = datetime.strptime(date, "%m/%d/%Y")
            day_name = date_obj.strftime("%A")
            if day_of_week_filter and day_name != day_of_week_filter:
                continue
        except ValueError:
            continue

        key = (court_name, date, start_time)
        booking_events[key].append({
            "status": status,
            "timestamp": last_updated,
            "location": location,
            "sport": sport,
            "day_of_week": day_name,
        })

    # Calculate booking velocities
    velocities = []

    for (court, date, time), events in booking_events.items():
        if len(events) < 2:
            continue

        # Sort by timestamp
        events.sort(key=lambda x: x["timestamp"])

        # Find first Available and first Unavailable after it
        first_available = None
        first_unavailable = None

        for event in events:
            if event["status"] == "Available" and first_available is None:
                first_available = event
            elif event["status"] == "Unavailable" and first_available is not None:
                first_unavailable = event
                break

        # Calculate velocity if we have both states
        if first_available and first_unavailable:
            try:
                time_available = datetime.strptime(first_available["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                time_available = datetime.strptime(first_available["timestamp"], "%Y-%m-%d %H:%M:%S")

            try:
                time_booked = datetime.strptime(first_unavailable["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                time_booked = datetime.strptime(first_unavailable["timestamp"], "%Y-%m-%d %H:%M:%S")

            booking_duration = (time_booked - time_available).total_seconds() / 60  # minutes

            velocities.append({
                "court": court,
                "date": date,
                "time_slot": time,
                "duration_minutes": booking_duration,
                "location": first_available["location"],
                "sport": first_available["sport"],
                "day_of_week": first_available["day_of_week"],
            })

    if not velocities:
        console.print("[yellow]No booking velocity data found.[/yellow]")
        console.print("[dim]💡 Continue monitoring to collect more data points[/dim]\n")
        return

    # Display results
    velocities.sort(key=lambda x: x["duration_minutes"])

    # Summary statistics
    avg_velocity = sum(v["duration_minutes"] for v in velocities) / len(velocities)
    fastest = velocities[0]
    slowest = velocities[-1]

    console.print(f"[green]Found {len(velocities)} booking transitions[/green]\n")

    console.print(f"⏱️  Average booking time: [bold]{avg_velocity:.1f} minutes[/bold]")
    console.print(f"⚡ Fastest booking: [bold]{fastest['duration_minutes']:.1f} minutes[/bold]")
    console.print(f"   {fastest['court']} on {fastest['date']} at {fastest['time_slot']}")
    console.print(f"🐌 Slowest booking: [bold]{slowest['duration_minutes']:.1f} minutes[/bold]")
    console.print(f"   {slowest['court']} on {slowest['date']} at {slowest['time_slot']}\n")

    # Top 10 fastest bookings
    console.print("[bold]⚡ Top 10 Fastest Bookings:[/bold]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Court", style="green")
    table.add_column("Date", style="yellow")
    table.add_column("Time", style="blue")
    table.add_column("Minutes to Book", style="red", justify="right")
    table.add_column("Day", style="magenta")

    for v in velocities[:10]:
        hours = v["duration_minutes"] / 60
        if hours < 1:
            duration_str = f"{v['duration_minutes']:.0f}m"
        else:
            duration_str = f"{hours:.1f}h"

        table.add_row(
            v["court"],
            v["date"],
            v["time_slot"],
            duration_str,
            v["day_of_week"],
        )

    console.print(table)
    console.print()


def _analyze_availability_patterns(
    db: Database,
    filter_clause: str,
    start_date: datetime,
    end_date: datetime,
    day_of_week_filter: Optional[str],
):
    """Analyze availability patterns by day of week and time."""

    console.print("[bold cyan]📅 Availability Patterns[/bold cyan]\n")

    # Query courts data
    query = f"""
        SELECT
            name,
            location,
            sport_type,
            date,
            availability_status,
            time_slot
        FROM courts
        WHERE {filter_clause}
        AND date BETWEEN ? AND ?
        ORDER BY date
    """

    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute(query, (start_date.strftime("%m/%d/%Y"), end_date.strftime("%m/%d/%Y")))
    rows = cursor.fetchall()

    if not rows:
        console.print("[yellow]No data available for analysis.[/yellow]\n")
        return

    # Analyze by day of week
    day_stats = defaultdict(lambda: {"available": 0, "booked": 0})

    for row in rows:
        name, location, sport, date, status, time_slot_summary = row

        try:
            date_obj = datetime.strptime(date, "%m/%d/%Y")
            day_name = date_obj.strftime("%A")

            if day_of_week_filter and day_name != day_of_week_filter:
                continue

            if status == "Available":
                day_stats[day_name]["available"] += 1
            elif status == "Fully Booked":
                day_stats[day_name]["booked"] += 1

        except ValueError:
            continue

    # Display day of week patterns
    if day_stats:
        console.print("[bold]📊 Availability by Day of Week:[/bold]")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Day", style="yellow")
        table.add_column("Available", style="green", justify="right")
        table.add_column("Fully Booked", style="red", justify="right")
        table.add_column("Availability %", style="blue", justify="right")

        # Sort by day of week
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in day_order:
            if day in day_stats:
                stats = day_stats[day]
                total = stats["available"] + stats["booked"]
                pct = (stats["available"] / total * 100) if total > 0 else 0

                table.add_row(
                    day,
                    str(stats["available"]),
                    str(stats["booked"]),
                    f"{pct:.1f}%",
                )

        console.print(table)
        console.print()

    console.print("[dim]💡 Use --day-of-week to focus on specific days[/dim]")
    console.print("[dim]💡 Use --time-slot to analyze specific time periods[/dim]\n")
