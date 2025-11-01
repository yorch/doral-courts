#!/usr/bin/env python3
"""Quick database viewer script for Doral Courts database."""

import sqlite3
import sys
from pathlib import Path


def view_database(db_path="doral_courts.db", limit=50):
    """View database contents in a formatted way."""

    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get total count
    cursor.execute("SELECT COUNT(*) FROM courts")
    total = cursor.fetchone()[0]

    print(f"\n📊 Database Overview")
    print(f"{'='*60}")
    print(f"Total Records: {total}")

    if total == 0:
        print("\n⚠️  Database is empty. Run 'doral-courts list' to fetch data.")
        conn.close()
        return

    # Get date range
    cursor.execute("SELECT MIN(date), MAX(date) FROM courts")
    min_date, max_date = cursor.fetchone()
    print(f"Date Range: {min_date} to {max_date}")

    # Sport breakdown
    cursor.execute("SELECT sport_type, COUNT(*) FROM courts GROUP BY sport_type")
    print(f"\nSport Breakdown:")
    for sport, count in cursor.fetchall():
        print(f"  • {sport}: {count} records")

    # Status breakdown
    cursor.execute("SELECT availability_status, COUNT(*) FROM courts GROUP BY availability_status")
    print(f"\nAvailability Status:")
    for status, count in cursor.fetchall():
        print(f"  • {status}: {count} records")

    # Recent records
    print(f"\n📋 Recent Records (Last {limit}):")
    print(f"{'='*60}")
    cursor.execute("""
        SELECT name, sport_type, date, availability_status, last_updated
        FROM courts
        ORDER BY last_updated DESC
        LIMIT ?
    """, (limit,))

    print(f"{'Court Name':<30} {'Sport':<12} {'Date':<12} {'Status':<20} {'Updated':<20}")
    print(f"{'-'*30} {'-'*12} {'-'*12} {'-'*20} {'-'*20}")

    for row in cursor.fetchall():
        name, sport, date, status, updated = row
        # Truncate long names
        display_name = name[:27] + "..." if len(name) > 30 else name
        updated_short = updated.split('.')[0] if updated else ""  # Remove microseconds
        print(f"{display_name:<30} {sport:<12} {date:<12} {status:<20} {updated_short:<20}")

    # Time slots analysis
    cursor.execute("SELECT COUNT(*) FROM time_slots")
    time_slots_total = cursor.fetchone()[0]

    if time_slots_total > 0:
        print(f"\n⏰ Time Slots Details")
        print(f"{'='*60}")
        print(f"Total Time Slot Records: {time_slots_total:,}")

        # Status breakdown
        cursor.execute("SELECT status, COUNT(*) FROM time_slots GROUP BY status")
        print(f"\nTime Slot Status:")
        for status, count in cursor.fetchall():
            percentage = (count / time_slots_total) * 100
            print(f"  • {status}: {count:,} ({percentage:.1f}%)")

        # Recent date with most detail
        cursor.execute("""
            SELECT date, COUNT(*) as slot_count
            FROM time_slots
            GROUP BY date
            ORDER BY last_updated DESC
            LIMIT 1
        """)
        recent_date, slot_count = cursor.fetchone()

        print(f"\n📅 Most Recent Date with Time Slots: {recent_date}")
        print(f"   Total slots recorded: {slot_count}")

        # Sample time slots for recent date
        cursor.execute("""
            SELECT c.name, ts.start_time, ts.end_time, ts.status
            FROM time_slots ts
            JOIN courts c ON ts.court_id = c.id
            WHERE ts.date = ?
            ORDER BY c.name, ts.start_time
            LIMIT 5
        """, (recent_date,))

        print(f"\n   Sample time slots:")
        for court_name, start, end, status in cursor.fetchall():
            status_symbol = "✅" if status == "Available" else "❌"
            court_short = court_name[:25] + "..." if len(court_name) > 28 else court_name
            print(f"   {status_symbol} {court_short:<28} {start} - {end}")

    conn.close()
    print(f"\n💡 Use 'sqlite3 {db_path}' for custom SQL queries")
    print(f"💡 Use 'uv run doral-courts history' for filtered views")
    print(f"💡 Use 'uv run doral-courts slots' for detailed time slot views\n")


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "doral_courts.db"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    view_database(db_path, limit)
