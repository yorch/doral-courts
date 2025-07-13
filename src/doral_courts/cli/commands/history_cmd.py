"""History command implementation."""

from typing import Optional

import click
from rich.console import Console

from ...core.database import Database
from ...display.detailed import (display_detailed_court_data,
                                 display_time_slots_summary)
from ...display.tables import display_courts_table
from ...utils.date_utils import parse_date_input
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
    "--status",
    type=click.Choice(["available", "booked", "maintenance"], case_sensitive=False),
    help="Filter by availability status",
)
@click.option(
    "--date",
    help="Date to check (default: today). Supports MM/DD/YYYY, today, tomorrow, yesterday, +N, -N",
)
@click.option(
    "--mode",
    type=click.Choice(["table", "detailed", "summary"], case_sensitive=False),
    default="table",
    help="Display mode: table (simple), detailed (full info), or summary (analysis)",
)
@click.pass_context
def history(
    ctx, sport: Optional[str], status: Optional[str], date: Optional[str], mode: str
):
    """View historical court data from database (cached data)."""
    # Parse date input
    try:
        parsed_date = parse_date_input(date)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    logger.info("Starting historical data display from database")
    logger.debug(
        f"Filters - Sport: {sport}, Status: {status}, Date: {date} -> {parsed_date}, Mode: {mode}"
    )

    db = Database()

    # Get courts from database with filters
    logger.debug("Retrieving historical data from database")
    courts = db.get_courts(
        sport_type=sport.title() if sport else None,
        availability_status=status.title() if status else None,
        date=parsed_date,
    )

    logger.info(f"Found {len(courts)} historical records matching criteria")

    if not courts:
        console.print(
            "[red]No historical court data found matching your criteria.[/red]"
        )
        console.print(
            "[blue]Try running other commands to fetch fresh data first.[/blue]"
        )
        return

    # Display historical data based on mode
    if mode == "table":
        # Simple table display
        display_courts_table(courts)
    elif mode == "detailed":
        # Detailed display with database note
        display_url = "Database (historical data)"
        display_detailed_court_data(courts, display_url)
    else:  # summary mode
        # Summary analysis with database note
        display_url = "Database (historical data)"
        display_time_slots_summary(courts, display_url)
