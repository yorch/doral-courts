"""List available slots command implementation."""

from typing import Optional

import click
from rich.console import Console

from ...display.tables import display_available_slots_table
from ...utils.date_utils import parse_date_input
from ...utils.logger import get_logger
from .._shared import fetch_and_store

logger = get_logger(__name__)
console = Console()


@click.command(name="list-available-slots")
@click.option(
    "--date",
    help=(
        "Date to check (default: today). Supports"
        " MM/DD/YYYY, today, tomorrow, yesterday, +N, -N"
    ),
)
@click.option(
    "--sport",
    type=click.Choice(["tennis", "pickleball"], case_sensitive=False),
    help="Filter by sport type",
)
@click.option("--location", help='Filter by location (e.g., "Doral Central Park")')
@click.pass_context
def list_available_slots(
    ctx: click.Context,
    date: Optional[str],
    sport: Optional[str],
    location: Optional[str],
) -> None:
    """List all available time slots by court for a specific date."""
    # Parse date input
    try:
        parsed_date = parse_date_input(date)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    logger.info("Starting available slots listing - fetching fresh data")
    logger.debug(f"Date: {date} -> {parsed_date}, Sport: {sport}, Location: {location}")

    # Fetch fresh data (sport filtering is applied by the scraper), store it,
    # and optionally save it to disk.
    courts, source_url = fetch_and_store(
        ctx, parsed_date, sport=sport, suffix="_available_slots"
    )
    if not courts:
        return

    # Apply remaining filters to fresh data
    logger.debug("Applying filters to fresh data")
    filtered_courts = courts

    if location:
        filtered_courts = [
            court
            for court in filtered_courts
            if location.lower() in court.location.lower()
        ]
        logger.debug(
            f"Applied location filter '{location}': {len(filtered_courts)} courts"
        )

    logger.info(f"Found {len(filtered_courts)} courts for available slots display")

    if not filtered_courts:
        console.print("[red]No courts found matching your criteria.[/red]")
        return

    # Display available slots table
    display_available_slots_table(filtered_courts, parsed_date, source_url)
