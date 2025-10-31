"""List command implementation."""

from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...core.database import Database
from ...core.scraper import Scraper
from ...display.tables import display_courts_table
from ...utils.date_utils import parse_date_input
from ...utils.file_utils import save_html_data, save_json_data
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
@click.pass_context
def list_courts(ctx, sport: Optional[str], status: Optional[str], date: Optional[str]):
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
    verbose = ctx.obj.get("verbose", False)

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

    db = Database()

    # Always fetch fresh data from website
    logger.info("Fetching fresh data from website")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching court data...", total=None)

        scraper = Scraper()

        # Check if we should save data
        save_data = ctx.obj.get("save_data", False)
        if save_data:
            courts, html_content = scraper.fetch_courts_with_html(
                date=parsed_date, sport_filter=sport
            )
        else:
            courts = scraper.fetch_courts(date=parsed_date, sport_filter=sport)
            html_content = ""

        if courts:
            logger.info(f"Successfully fetched {len(courts)} courts from website")
            # Store in database for historical tracking
            inserted_count = db.insert_courts(courts)
            logger.debug(
                f"Inserted/updated {inserted_count} courts in database for tracking"
            )
            progress.update(task, description=f"Fetched {len(courts)} courts")

            # Save data if requested
            if save_data:
                try:
                    html_path = save_html_data(html_content, "_list")
                    json_path = save_json_data(
                        courts, "_list", scraper.get_last_request_url()
                    )
                    console.print(f"[green]Data saved to:[/green]")
                    console.print(f"  HTML: {html_path}")
                    console.print(f"  JSON: {json_path}")
                except Exception as e:
                    logger.error(f"Error saving data: {e}")
                    console.print(f"[red]Error saving data: {e}[/red]")
        else:
            logger.error("No court data could be retrieved from website")
            console.print("[red]Unable to fetch court data from website.[/red]")
            console.print(
                "[yellow]The website may be temporarily unavailable or blocking requests.[/yellow]"
            )
            return

    # Apply filters to fresh data
    logger.debug("Applying filters to fresh data")
    filtered_courts = courts

    if sport:
        filtered_courts = [
            court
            for court in filtered_courts
            if court.sport_type.lower() == sport.lower()
        ]
        logger.debug(
            f"Applied sport filter '{sport}': {len(courts)} -> {len(filtered_courts)} courts"
        )

    if status:
        filtered_courts = [
            court
            for court in filtered_courts
            if status.lower() in court.availability_status.lower()
        ]
        logger.debug(f"Applied status filter '{status}': {len(filtered_courts)} courts")

    logger.info(f"Found {len(filtered_courts)} courts matching criteria")

    if not filtered_courts:
        console.print("[red]No courts found matching your criteria.[/red]")
        return

    # Display courts in a table
    logger.debug("Displaying courts table")
    display_courts_table(filtered_courts)
