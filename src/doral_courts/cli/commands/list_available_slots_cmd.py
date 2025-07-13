"""List available slots command implementation."""

from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...core.database import Database
from ...core.scraper import Scraper
from ...display.tables import display_available_slots_table
from ...utils.date_utils import parse_date_input
from ...utils.file_utils import save_html_data, save_json_data
from ...utils.logger import get_logger

logger = get_logger(__name__)
console = Console()


@click.command(name="list-available-slots")
@click.option(
    "--date",
    help="Date to check (default: today). Supports MM/DD/YYYY, today, tomorrow, yesterday, +N, -N",
)
@click.option(
    "--sport",
    type=click.Choice(["tennis", "pickleball"], case_sensitive=False),
    help="Filter by sport type",
)
@click.option("--location", help='Filter by location (e.g., "Doral Central Park")')
@click.pass_context
def list_available_slots(
    ctx, date: Optional[str], sport: Optional[str], location: Optional[str]
):
    """List all available time slots by court for a specific date."""
    # Parse date input
    try:
        parsed_date = parse_date_input(date)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    logger.info("Starting available slots listing - fetching fresh data")
    logger.debug(f"Date: {date} -> {parsed_date}, Sport: {sport}, Location: {location}")

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
                    html_path = save_html_data(html_content, "_available_slots")
                    json_path = save_json_data(
                        courts, "_available_slots", scraper.get_last_request_url()
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
    display_available_slots_table(
        filtered_courts, parsed_date, scraper.get_last_request_url()
    )
