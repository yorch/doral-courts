"""List display functions."""

from typing import List, Optional

from rich.console import Console
from rich.table import Table

from ..core.html_extractor import Court

console = Console()


def display_courts_list(courts: List[Court], sport_filter: Optional[str] = None):
    """Display a simple list of unique court names."""
    if not courts:
        console.print("[red]No court data available.[/red]")
        return

    # Extract unique court names
    court_names = set()
    for court in courts:
        if sport_filter:
            if court.sport_type.lower() == sport_filter.lower():
                court_names.add(court.name)
        else:
            court_names.add(court.name)

    if not court_names:
        if sport_filter:
            console.print(f"[red]No {sport_filter} courts found.[/red]")
        else:
            console.print("[red]No courts found.[/red]")
        return

    # Sort court names
    sorted_courts = sorted(court_names)

    console.print(f"\n[bold blue]🏟️  Available Courts[/bold blue]")
    if sport_filter:
        console.print(f"[dim]Filtered by sport: {sport_filter.title()}[/dim]")
    console.print(f"[cyan]Total: {len(sorted_courts)} courts[/cyan]\n")

    # Create a simple table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Court Name", style="cyan")

    for i, court_name in enumerate(sorted_courts, 1):
        table.add_row(str(i), court_name)

    console.print(table)


def display_locations_list(courts: List[Court], sport_filter: Optional[str] = None):
    """Display a list of unique locations with court counts."""
    if not courts:
        console.print("[red]No court data available.[/red]")
        return

    # Count courts by location
    location_counts = {}
    for court in courts:
        if sport_filter:
            if court.sport_type.lower() == sport_filter.lower():
                location = court.location
                if location not in location_counts:
                    location_counts[location] = 0
                location_counts[location] += 1
        else:
            location = court.location
            if location not in location_counts:
                location_counts[location] = 0
            location_counts[location] += 1

    if not location_counts:
        if sport_filter:
            console.print(f"[red]No locations found for {sport_filter} courts.[/red]")
        else:
            console.print("[red]No locations found.[/red]")
        return

    # Sort locations by name
    sorted_locations = sorted(location_counts.items())

    console.print(f"\n[bold blue]📍 Available Locations[/bold blue]")
    if sport_filter:
        console.print(f"[dim]Filtered by sport: {sport_filter.title()}[/dim]")

    total_locations = len(sorted_locations)
    total_courts = sum(location_counts.values())
    console.print(
        f"[cyan]Total: {total_locations} locations with {total_courts} courts[/cyan]\n"
    )

    # Create a table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Location", style="cyan")
    table.add_column("Court Count", style="green", justify="right")

    for i, (location, count) in enumerate(sorted_locations, 1):
        table.add_row(str(i), location, str(count))

    console.print(table)
