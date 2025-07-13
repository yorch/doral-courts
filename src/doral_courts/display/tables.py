"""Table display utilities for courts data."""

from typing import List

from rich.console import Console
from rich.table import Table

from ..core.html_extractor import Court

console = Console()


def display_courts_table(courts: List[Court]):
    """
    Display courts in a formatted Rich table.

    Creates and displays a comprehensive table showing court information
    including availability, time slots, and other details. Uses Rich library
    for colored output and proper formatting.

    Args:
        courts: List of Court objects to display

    Table Columns:
        - Court Name: Name of the court (cyan, no-wrap)
        - Sport: Tennis or Pickleball (magenta)
        - Date: Date being displayed (green)
        - Time Slots: Available/total count (yellow)
        - Status: Availability status with color coding (bold)
        - Capacity: Maximum players (blue)
        - Price: Cost information (green)

    Color Coding:
        - Green status: Courts with available slots
        - Red status: Fully booked courts
        - Yellow status: Other statuses (maintenance, etc.)

    Example:
        courts = scraper.fetch_courts()
        display_courts_table(courts)
    """
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
            available_count = sum(
                1 for slot in court.time_slots if slot.status == "Available"
            )
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
            court.price or "N/A",
        )

    console.print(table)


def display_available_slots_table(
    courts: List[Court], date: str, source_url: str = None
):
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
        available_slots = [
            slot for slot in court.time_slots if slot.status == "Available"
        ]

        for slot in available_slots:
            available_slots_data.append(
                {
                    "court_name": court.name,
                    "location": court.location,
                    "sport": court.sport_type,
                    "capacity": court.capacity,
                    "start_time": slot.start_time,
                    "end_time": slot.end_time,
                    "price": court.price or "N/A",
                }
            )

    if not available_slots_data:
        console.print(f"[yellow]No available time slots found for {date}.[/yellow]")
        console.print("[dim]All courts may be fully booked for this date.[/dim]")
        return

    # Sort by start time, then by court name
    available_slots_data.sort(key=lambda x: (x["start_time"], x["court_name"]))

    # Create summary statistics
    total_slots = len(available_slots_data)
    unique_courts = len(set(slot["court_name"] for slot in available_slots_data))
    sports_breakdown = {}
    location_breakdown = {}

    for slot in available_slots_data:
        sport = slot["sport"]
        location = slot["location"]

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
            slot_data["court_name"],
            slot_data["sport"],
            slot_data["location"],
            slot_data["capacity"],
            slot_data["price"],
        )

    console.print(f"\n[bold green]📋 Detailed Schedule:[/bold green]")
    console.print(table)

    # Add helpful footer
    console.print(
        f"\n[dim]💡 Tip: Use --sport or --location filters to narrow down results[/dim]"
    )
