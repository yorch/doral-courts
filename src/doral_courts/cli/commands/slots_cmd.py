"""Slots command implementation."""

from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from ...utils.date_utils import parse_date_input
from ...utils.logger import get_logger
from .._shared import fetch_and_store

logger = get_logger(__name__)
console = Console()


@click.command()
@click.option("--court", help="Show detailed time slots for a specific court")
@click.option(
    "--date",
    help=(
        "Date to check (default: today). "
        "Supports MM/DD/YYYY, today, tomorrow, yesterday, +N, -N"
    ),
)
@click.option("--available-only", is_flag=True, help="Show only available time slots")
@click.pass_context
def slots(
    ctx: click.Context,
    court: Optional[str],
    date: Optional[str],
    available_only: bool,
) -> None:
    """Show detailed time slot availability for courts. Always fetches fresh data."""
    # Parse date input
    try:
        parsed_date = parse_date_input(date)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    logger.info("Starting detailed time slots display - fetching fresh data")
    logger.debug(
        "Filters - Court: %s, Date: %s -> %s, Available only: %s",
        court,
        date,
        parsed_date,
        available_only,
    )

    # Fetch fresh data, store it, and optionally save it to disk.
    courts, _ = fetch_and_store(ctx, parsed_date, suffix="_slots")
    if not courts:
        return

    # Apply court filter to fresh data
    if court:
        courts = [c for c in courts if court.lower() in c.name.lower()]
        if not courts:
            console.print(f"[red]No courts found matching '{court}'[/red]")
            return

    if not courts:
        console.print("[red]No courts found matching your criteria.[/red]")
        return

    for court_obj in courts:
        if not court_obj.time_slots:
            console.print(
                f"\n[yellow]{court_obj.name} - No time slots available[/yellow]"
            )
            continue

        # Filter slots if needed
        slots_to_show = court_obj.time_slots
        if available_only:
            slots_to_show = [
                slot for slot in court_obj.time_slots if slot.status == "Available"
            ]

        if not slots_to_show and available_only:
            console.print(
                f"\n[yellow]{court_obj.name} - No available time slots[/yellow]"
            )
            continue

        # Create table for this court's time slots
        table = Table(title=f"{court_obj.name} - {court_obj.date}")
        table.add_column("Start Time", style="cyan")
        table.add_column("End Time", style="cyan")
        table.add_column("Status", style="bold")

        for slot in slots_to_show:
            # Color code the status
            if slot.status == "Available":
                status_style = "[green]"
            else:
                status_style = "[red]"

            table.add_row(
                slot.start_time, slot.end_time, f"{status_style}{slot.status}[/]"
            )

        console.print(table)
