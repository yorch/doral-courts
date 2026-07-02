"""List command implementation."""

from typing import Optional

import click
from rich.console import Console

from ...display.tables import display_courts_table
from ...utils.config import Config
from ...utils.date_utils import parse_date_input
from ...utils.logger import get_logger
from .._shared import fetch_and_store

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
    help=(
        "Date to check (default: today). Supports"
        " MM/DD/YYYY, today, tomorrow, yesterday, +N, -N"
    ),
)
@click.option(
    "--favorites",
    is_flag=True,
    help="Show only favorite courts",
)
@click.pass_context
def list_courts(
    ctx: click.Context,
    sport: Optional[str],
    status: Optional[str],
    date: Optional[str],
    favorites: bool,
) -> None:
    """
    List available courts with optional filters. Always fetches fresh data from website.

    Retrieves current court availability data from the Doral reservation system
    and displays it in a formatted table. Supports filtering by sport type,
    availability status, and date.

    Args:
        ctx: Click context with global options
        sport: Filter results to show only tennis or pickleball courts
        status: Filter by availability status (available, booked, maintenance)
        date: Date to check in various formats (default: today)

    Date Formats:
        - Relative: today, tomorrow, yesterday
        - Offset: +N, -N (days from today)
        - Absolute: MM/DD/YYYY, YYYY-MM-DD

    Output:
        Displays a Rich table with columns:
        - Court Name: Name of the court
        - Sport: Tennis or Pickleball
        - Date: Date being checked
        - Time Slots: Available/total slots
        - Status: Overall availability
        - Capacity: Maximum players
        - Price: Cost information

    Examples:
        doral-courts list
        doral-courts list --sport tennis --date tomorrow
        doral-courts list --status available --date +7

    Note:
        Always fetches fresh data from the website. For historical data,
        use the 'history' command instead.
    """
    # Parse date input
    try:
        parsed_date = parse_date_input(date)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    logger.info("Starting court listing command - fetching fresh data")
    logger.debug(
        f"Filters - Sport: {sport}, Status: {status}, Date: {date} -> {parsed_date}"
    )

    # Fetch fresh data (sport filtering is applied by the scraper), store it,
    # and optionally save it to disk.
    courts, _ = fetch_and_store(ctx, parsed_date, sport=sport, suffix="_list")
    if not courts:
        return

    # Apply remaining filters to fresh data
    logger.debug("Applying filters to fresh data")
    filtered_courts = courts

    if status:
        filtered_courts = [
            court
            for court in filtered_courts
            if status.lower() in court.availability_status.lower()
        ]
        logger.debug(f"Applied status filter '{status}': {len(filtered_courts)} courts")

    if favorites:
        config = Config()
        favorite_court_names = config.get_favorites()
        if not favorite_court_names:
            console.print("[yellow]No favorite courts configured.[/yellow]")
            console.print(
                "[blue]Add favorites with: doral-courts"
                " favorites add <court_name>[/blue]"
            )
            return

        filtered_courts = [
            court for court in filtered_courts if court.name in favorite_court_names
        ]
        logger.debug(
            f"Applied favorites filter: {len(filtered_courts)} courts in favorites"
        )

    logger.info(f"Found {len(filtered_courts)} courts matching criteria")

    if not filtered_courts:
        console.print("[red]No courts found matching your criteria.[/red]")
        return

    # Display courts in a table with favorite highlighting
    logger.debug("Displaying courts table")
    config = Config()
    favorites_for_display = set(config.get_favorites())
    display_courts_table(filtered_courts, favorites_for_display)
