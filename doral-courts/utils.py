import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from html_extractor import Court
from logger import get_logger
import re

logger = get_logger(__name__)
console = Console()

def parse_date_input(date_input: Optional[str] = None) -> str:
    """
    Parse date input supporting both absolute and relative formats.

    Args:
        date_input: Date string in various formats:
                   - None: defaults to today
                   - "today", "now": today
                   - "tomorrow": tomorrow
                   - "yesterday": yesterday
                   - "+N": N days from today (e.g., "+3")
                   - "-N": N days before today (e.g., "-2")
                   - "MM/DD/YYYY": absolute date

    Returns:
        Date string in MM/DD/YYYY format

    Raises:
        ValueError: If date format is invalid
    """
    if date_input is None or date_input.lower() in ["today", "now"]:
        target_date = datetime.now()
    elif date_input.lower() == "tomorrow":
        target_date = datetime.now() + timedelta(days=1)
    elif date_input.lower() == "yesterday":
        target_date = datetime.now() - timedelta(days=1)
    elif re.match(r'^[+-]\d+$', date_input):
        # Handle relative days like +3, -2
        days_offset = int(date_input)
        target_date = datetime.now() + timedelta(days=days_offset)
    elif re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_input):
        # Handle MM/DD/YYYY format - validate it
        try:
            target_date = datetime.strptime(date_input, "%m/%d/%Y")
        except ValueError:
            raise ValueError(f"Invalid date format: {date_input}. Use MM/DD/YYYY format.")
    else:
        # Try to parse other common formats
        common_formats = [
            "%Y-%m-%d",      # 2025-07-12
            "%m-%d-%Y",      # 07-12-2025
            "%d/%m/%Y",      # 12/07/2025 (European)
            "%Y/%m/%d",      # 2025/07/12
        ]

        target_date = None
        for fmt in common_formats:
            try:
                target_date = datetime.strptime(date_input, fmt)
                break
            except ValueError:
                continue

        if target_date is None:
            raise ValueError(
                f"Invalid date format: {date_input}. "
                f"Supported formats: MM/DD/YYYY, today, tomorrow, yesterday, +N, -N"
            )

    # Return in MM/DD/YYYY format that the website expects
    return target_date.strftime("%m/%d/%Y")

def save_html_data(html_content: str, filename_suffix: str = "") -> str:
    """Save HTML content to a file in the data directory."""
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"doral_courts_{timestamp}{filename_suffix}.html"
    filepath = data_dir / filename

    # Save HTML content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logger.info(f"Saved HTML data to {filepath}")
    return str(filepath)

def save_json_data(courts: List[Court], filename_suffix: str = "", source_url: str = None) -> str:
    """Save court data as JSON to a file in the data directory."""
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"doral_courts_{timestamp}{filename_suffix}.json"
    filepath = data_dir / filename

    # Convert courts to JSON-serializable format
    courts_data = []
    for court in courts:
        court_dict = {
            "name": court.name,
            "sport_type": court.sport_type,
            "location": court.location,
            "capacity": court.capacity,
            "availability_status": court.availability_status,
            "date": court.date,
            "price": court.price,
            "time_slots": [
                {
                    "start_time": slot.start_time,
                    "end_time": slot.end_time,
                    "status": slot.status
                }
                for slot in court.time_slots
            ]
        }
        courts_data.append(court_dict)

    # Create the full data structure
    json_data = {
        "timestamp": datetime.now().isoformat(),
        "total_courts": len(courts),
        "source_url": source_url,
        "courts": courts_data
    }

    # Save JSON content
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved JSON data to {filepath}")
    return str(filepath)

def display_courts_table(courts: List[Court]):
    """Display courts in a formatted table."""
    table = Table(title="Doral Courts Availability")

    table.add_column("Court Name", style="cyan", no_wrap=True)
    table.add_column("Sport", style="magenta")
    table.add_column("Date", style="green")
    table.add_column("Time Slots", style="yellow")
    table.add_column("Status", style="bold")
    table.add_column("Capacity", style="blue")
    table.add_column("Price", style="green")

    for court in courts:
        # Color code the status
        if "available" in court.availability_status.lower():
            status_style = "[green]"
        elif "booked" in court.availability_status.lower():
            status_style = "[red]"
        else:
            status_style = "[yellow]"

        # Format time slots display
        if court.time_slots:
            available_count = sum(1 for slot in court.time_slots if slot.status == "Available")
            total_count = len(court.time_slots)
            time_display = f"{available_count}/{total_count} available"
        else:
            time_display = "No slots"

        table.add_row(
            court.name,
            court.sport_type,
            court.date,
            time_display,
            f"{status_style}{court.availability_status}[/]",
            court.capacity,
            court.price or "N/A"
        )

    console.print(table)

def display_detailed_court_data(courts: List[Court], base_url: str = None):
    """Display comprehensive court data with all scraped information."""
    if not courts:
        console.print("[red]No court data available.[/red]")
        return

    console.print(f"\n[bold blue]📊 Complete Scraped Data Summary[/bold blue]")
    console.print(f"Total Courts Found: [bold]{len(courts)}[/bold]")

    # Display data source URL if available
    if base_url:
        console.print(f"[dim]Data Source: {base_url}[/dim]")

    # Group courts by location and sport
    locations = {}
    sports = {}
    for court in courts:
        # Group by location
        if court.location not in locations:
            locations[court.location] = []
        locations[court.location].append(court)

        # Count by sport
        if court.sport_type not in sports:
            sports[court.sport_type] = 0
        sports[court.sport_type] += 1

    # Display summary statistics
    console.print(f"\n[bold cyan]🏟️  Locations & Courts:[/bold cyan]")
    for location, location_courts in locations.items():
        console.print(f"  • {location}: [green]{len(location_courts)}[/green] courts")

    console.print(f"\n[bold magenta]🎾 Sports Breakdown:[/bold magenta]")
    for sport, count in sports.items():
        console.print(f"  • {sport}: [green]{count}[/green] courts")

    # Display detailed information for each court
    console.print(f"\n[bold yellow]📋 Detailed Court Information:[/bold yellow]")

    for i, court in enumerate(courts, 1):
        # Create a panel for each court with all details
        court_info = f"""[bold]Court #{i}[/bold]
[cyan]Name:[/cyan] {court.name}
[cyan]Sport:[/cyan] {court.sport_type}
[cyan]Location:[/cyan] {court.location}
[cyan]Capacity:[/cyan] {court.capacity}
[cyan]Date:[/cyan] {court.date}
[cyan]Status:[/cyan] {court.availability_status}
[cyan]Price:[/cyan] {court.price or 'N/A'}
[cyan]Total Time Slots:[/cyan] {len(court.time_slots)}"""

        if court.time_slots:
            available_slots = [slot for slot in court.time_slots if slot.status == "Available"]
            unavailable_slots = [slot for slot in court.time_slots if slot.status == "Unavailable"]

            court_info += f"""
[cyan]Available Slots:[/cyan] [green]{len(available_slots)}[/green]
[cyan]Unavailable Slots:[/cyan] [red]{len(unavailable_slots)}[/red]"""

            # Show first few time slots as examples
            if len(court.time_slots) > 0:
                court_info += f"\n[cyan]Sample Time Slots:[/cyan]"
                for j, slot in enumerate(court.time_slots[:3]):  # Show first 3 slots
                    status_color = "[green]" if slot.status == "Available" else "[red]"
                    court_info += f"\n  • {slot.start_time} - {slot.end_time}: {status_color}{slot.status}[/]"

                if len(court.time_slots) > 3:
                    court_info += f"\n  ... and {len(court.time_slots) - 3} more slots"

        # Color-code the panel based on availability
        if "available" in court.availability_status.lower():
            panel_style = "green"
        elif "booked" in court.availability_status.lower():
            panel_style = "red"
        else:
            panel_style = "yellow"

        panel = Panel(court_info, title=court.name, border_style=panel_style)
        console.print(panel)

        # Add spacing between courts, but not after the last one
        if i < len(courts):
            console.print()

def display_time_slots_summary(courts: List[Court], base_url: str = None):
    """Display a summary of all time slots across all courts."""
    if not courts:
        console.print("[red]No court data available.[/red]")
        return

    all_slots = []
    for court in courts:
        for slot in court.time_slots:
            all_slots.append({
                'court': court.name,
                'location': court.location,
                'sport': court.sport_type,
                'start_time': slot.start_time,
                'end_time': slot.end_time,
                'status': slot.status,
                'date': court.date
            })

    if not all_slots:
        console.print("[yellow]No time slots found in scraped data.[/yellow]")
        return

    console.print(f"\n[bold blue]🕐 Time Slots Analysis[/bold blue]")
    console.print(f"Total Time Slots: [bold]{len(all_slots)}[/bold]")

    # Display data source URL if available
    if base_url:
        console.print(f"[dim]Data Source: {base_url}[/dim]")

    # Count available vs unavailable
    available_count = sum(1 for slot in all_slots if slot['status'] == 'Available')
    unavailable_count = len(all_slots) - available_count

    console.print(f"Available: [green]{available_count}[/green] ({available_count/len(all_slots)*100:.1f}%)")
    console.print(f"Unavailable: [red]{unavailable_count}[/red] ({unavailable_count/len(all_slots)*100:.1f}%)")

    # Group by time range to show popular times
    time_ranges = {}
    for slot in all_slots:
        time_key = f"{slot['start_time']} - {slot['end_time']}"
        if time_key not in time_ranges:
            time_ranges[time_key] = {'total': 0, 'available': 0}
        time_ranges[time_key]['total'] += 1
        if slot['status'] == 'Available':
            time_ranges[time_key]['available'] += 1

    # Show most common time slots
    sorted_times = sorted(time_ranges.items(), key=lambda x: x[1]['total'], reverse=True)

    console.print(f"\n[bold cyan]📊 Most Common Time Slots:[/bold cyan]")
    for i, (time_range, data) in enumerate(sorted_times[:10]):  # Top 10
        availability_pct = (data['available'] / data['total']) * 100 if data['total'] > 0 else 0
        console.print(f"  {i+1:2d}. {time_range}: {data['total']} slots ({availability_pct:.0f}% available)")

    if len(sorted_times) > 10:
        console.print(f"  ... and {len(sorted_times) - 10} more unique time ranges")

def display_available_slots_table(courts: List[Court], date: str, source_url: str = None):
    """Display available time slots per court in a comprehensive table format."""
    if not courts:
        console.print("[red]No court data available.[/red]")
        return

    console.print(f"\n[bold blue]📅 Available Time Slots for {date}[/bold blue]")

    # Display data source URL if available
    if source_url:
        console.print(f"[dim]Data Source: {source_url}[/dim]")

    # Collect all available slots with court information
    available_slots_data = []

    for court in courts:
        available_slots = [slot for slot in court.time_slots if slot.status == "Available"]

        for slot in available_slots:
            available_slots_data.append({
                'court_name': court.name,
                'location': court.location,
                'sport': court.sport_type,
                'capacity': court.capacity,
                'start_time': slot.start_time,
                'end_time': slot.end_time,
                'price': court.price or "N/A"
            })

    if not available_slots_data:
        console.print(f"[yellow]No available time slots found for {date}.[/yellow]")
        console.print("[dim]All courts may be fully booked for this date.[/dim]")
        return

    # Sort by start time, then by court name
    available_slots_data.sort(key=lambda x: (x['start_time'], x['court_name']))

    # Create summary statistics
    total_slots = len(available_slots_data)
    unique_courts = len(set(slot['court_name'] for slot in available_slots_data))
    sports_breakdown = {}
    location_breakdown = {}

    for slot in available_slots_data:
        sport = slot['sport']
        location = slot['location']

        if sport not in sports_breakdown:
            sports_breakdown[sport] = 0
        sports_breakdown[sport] += 1

        if location not in location_breakdown:
            location_breakdown[location] = 0
        location_breakdown[location] += 1

    # Display summary
    console.print(f"\n[bold cyan]📊 Summary:[/bold cyan]")
    console.print(f"  • Total Available Slots: [green]{total_slots}[/green]")
    console.print(f"  • Courts with Availability: [green]{unique_courts}[/green]")

    console.print(f"\n[bold magenta]🎾 By Sport:[/bold magenta]")
    for sport, count in sports_breakdown.items():
        console.print(f"  • {sport}: [green]{count}[/green] slots")

    console.print(f"\n[bold yellow]🏢 By Location:[/bold yellow]")
    for location, count in location_breakdown.items():
        console.print(f"  • {location}: [green]{count}[/green] slots")

    # Create detailed table
    table = Table(title=f"Available Time Slots - {date}")

    table.add_column("Time", style="cyan", no_wrap=True)
    table.add_column("Court", style="bright_white", no_wrap=False)
    table.add_column("Sport", style="magenta")
    table.add_column("Location", style="blue")
    table.add_column("Capacity", style="yellow")
    table.add_column("Price", style="green")

    # Group slots by time for better readability
    current_time = None

    for slot_data in available_slots_data:
        time_range = f"{slot_data['start_time']} - {slot_data['end_time']}"

        # Add visual separator for new time slots
        if current_time != time_range:
            if current_time is not None:
                # Add a separator row (empty row with style)
                table.add_row("", "", "", "", "", "", style="dim")
            current_time = time_range

        table.add_row(
            time_range,
            slot_data['court_name'],
            slot_data['sport'],
            slot_data['location'],
            slot_data['capacity'],
            slot_data['price']
        )

    console.print(f"\n[bold green]📋 Detailed Schedule:[/bold green]")
    console.print(table)

    # Add helpful footer
    console.print(f"\n[dim]💡 Tip: Use --sport or --location filters to narrow down results[/dim]")
