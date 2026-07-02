"""List courts command implementation."""

from typing import Optional

import click
from rich.console import Console

from ...display.lists import display_courts_list
from ...utils.date_utils import parse_date_input
from ...utils.logger import get_logger
from .._shared import fetch_and_store

logger = get_logger(__name__)
console = Console()


@click.command(name="list-courts")
@click.option(
    "--sport",
    type=click.Choice(["tennis", "pickleball"], case_sensitive=False),
    help="Filter by sport type",
)
@click.option(
    "--date",
    help=(
        "Date to check (default: today). "
        "Supports MM/DD/YYYY, today, tomorrow, yesterday, +N, -N"
    ),
)
@click.pass_context
def list_courts(ctx: click.Context, sport: Optional[str], date: Optional[str]) -> None:
    """List all available court names."""
    # Parse date input
    try:
        parsed_date = parse_date_input(date)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    logger.info("Starting court names listing - fetching fresh data")
    logger.debug(f"Sport: {sport}, Date: {date} -> {parsed_date}")

    # Fetch fresh data (sport filtering is applied by the scraper), store it,
    # and optionally save it to disk.
    courts, _ = fetch_and_store(ctx, parsed_date, sport=sport, suffix="_list_courts")
    if not courts:
        return

    # Display courts list
    display_courts_list(courts, sport)
