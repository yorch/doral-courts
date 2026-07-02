"""Data command implementation."""

from typing import Optional

import click
from rich.console import Console

from ...display.detailed import display_detailed_court_data, display_time_slots_summary
from ...utils.date_utils import parse_date_input
from ...utils.logger import get_logger
from .._shared import fetch_and_store

logger = get_logger(__name__)
console = Console()


@click.command()
@click.option(
    "--mode",
    type=click.Choice(["detailed", "summary"], case_sensitive=False),
    default="detailed",
    help="Display mode: detailed (full court info) or summary (time slots analysis)",
)
@click.option(
    "--sport",
    type=click.Choice(["tennis", "pickleball"], case_sensitive=False),
    help="Filter by sport type",
)
@click.option(
    "--date",
    help=(
        "Date to check (default: today). Supports"
        " MM/DD/YYYY, today, tomorrow, yesterday, +N, -N"
    ),
)
@click.pass_context
def data(
    ctx: click.Context,
    mode: str,
    sport: Optional[str],
    date: Optional[str],
) -> None:
    """Display comprehensive view of all scraped data.

    Always fetches fresh data from the website.
    """
    # Parse date input
    try:
        parsed_date = parse_date_input(date)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    logger.info("Starting comprehensive data display - fetching fresh data")
    logger.debug("Mode: %s, Sport: %s, Date: %s -> %s", mode, sport, date, parsed_date)

    # Fetch fresh data (sport filtering is applied by the scraper), store it,
    # and optionally save it to disk.
    courts, actual_url = fetch_and_store(
        ctx,
        parsed_date,
        sport=sport,
        suffix="_data",
        description="Fetching latest data...",
    )
    if not courts:
        return

    logger.info("Found %s courts for comprehensive display", len(courts))

    # Display data based on mode
    if mode == "detailed":
        display_detailed_court_data(courts, actual_url)
    else:  # summary mode
        display_time_slots_summary(courts, actual_url)
