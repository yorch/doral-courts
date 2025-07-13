"""Detailed display functions for court data."""

from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..core.html_extractor import Court

console = Console()


def display_detailed_court_data(courts: List[Court], source_url: str):
    """Display comprehensive court data with full details."""
    console.print(
        f"\n[bold blue]Detailed Court Data ({len(courts)} courts)[/bold blue]"
    )
    console.print(f"[dim]Source: {source_url}[/dim]\n")

    for court in courts:
        # Create detailed panel for each court
        details = f"""[bold]{court.name}[/bold]
Sport: {court.sport_type}
Location: {court.location}
Date: {court.date}
Capacity: {court.capacity}
Price: {court.price}
Status: {court.availability_status}

Time Slots: {len(court.time_slots) if court.time_slots else 0} total"""

        if court.time_slots:
            available_slots = [
                slot for slot in court.time_slots if slot.status == "Available"
            ]
            details += f", {len(available_slots)} available"

            # Add time slot details
            details += "\n\nTime Slots:"
            for slot in court.time_slots:
                status_color = "green" if slot.status == "Available" else "red"
                details += f"\n  {slot.start_time}-{slot.end_time}: [{status_color}]{slot.status}[/]"

        panel = Panel(details, border_style="blue", title_align="left")
        console.print(panel)


def display_time_slots_summary(courts: List[Court], source_url: str):
    """Display time slots analysis summary."""
    console.print(f"\n[bold blue]Time Slots Summary ({len(courts)} courts)[/bold blue]")
    console.print(f"[dim]Source: {source_url}[/dim]\n")

    total_slots = 0
    available_slots = 0

    for court in courts:
        if court.time_slots:
            court_total = len(court.time_slots)
            court_available = len(
                [slot for slot in court.time_slots if slot.status == "Available"]
            )

            total_slots += court_total
            available_slots += court_available

            availability_pct = (
                (court_available / court_total * 100) if court_total > 0 else 0
            )

            console.print(f"[bold]{court.name}[/bold]")
            console.print(
                f"  {court_available}/{court_total} slots available ({availability_pct:.1f}%)"
            )
            console.print()

    # Overall summary
    overall_pct = (available_slots / total_slots * 100) if total_slots > 0 else 0
    summary = f"""Total Time Slots: {total_slots}
Available Slots: {available_slots}
Booked Slots: {total_slots - available_slots}
Overall Availability: {overall_pct:.1f}%"""

    panel = Panel(summary, title="Overall Summary", border_style="green")
    console.print(panel)
