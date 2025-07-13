"""List courts command implementation."""

from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...core.database import Database
from ...core.scraper import Scraper
from ...display.lists import display_courts_list
from ...utils.date_utils import parse_date_input
from ...utils.file_utils import save_html_data, save_json_data
from ...utils.logger import get_logger

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
    help="Date to check (default: today). Supports MM/DD/YYYY, today, tomorrow, yesterday, +N, -N",
)
@click.pass_context
def list_courts(ctx, sport: Optional[str], date: Optional[str]):
    """List all available court names."""
    # Parse date input
    try:
        parsed_date = parse_date_input(date)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    logger.info("Starting court names listing - fetching fresh data")
    logger.debug(f"Sport: {sport}, Date: {date} -> {parsed_date}")

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
                    html_path = save_html_data(html_content, "_list_courts")
                    json_path = save_json_data(
                        courts, "_list_courts", scraper.get_last_request_url()
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

    # Display courts list
    display_courts_list(courts, sport)
