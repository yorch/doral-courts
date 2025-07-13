"""Watch command implementation."""

import time
from datetime import datetime
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
    "--interval", default=300, help="Update interval in seconds (default: 5 minutes)"
)
@click.option(
    "--sport",
    type=click.Choice(["tennis", "pickleball"], case_sensitive=False),
    help="Filter by sport type",
)
@click.option(
    "--date",
    help="Date to monitor (default: today). Supports MM/DD/YYYY, today, tomorrow, yesterday, +N, -N",
)
@click.pass_context
def watch(ctx, interval: int, sport: Optional[str], date: Optional[str]):
    """Monitor court availability with real-time updates."""
    # Parse date input
    try:
        parsed_date = parse_date_input(date)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    logger.info(f"Starting watch mode with {interval}s interval")
    logger.debug(f"Watch filters - Sport: {sport}, Date: {date} -> {parsed_date}")

    console.print(
        f"[blue]Monitoring court availability every {interval} seconds. Press Ctrl+C to stop.[/blue]"
    )

    update_count = 0
    try:
        while True:
            update_count += 1
            logger.debug(f"Watch update #{update_count}")

            console.clear()
            console.print(
                f"[bold]Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/bold]\n"
            )

            db = Database()
            scraper = Scraper()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Fetching latest data...", total=None)

                logger.debug("Fetching fresh court data for watch update")

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
                    logger.debug(f"Fetched {len(courts)} courts for watch update")
                    inserted_count = db.insert_courts(courts)
                    logger.debug(f"Updated {inserted_count} courts in database")
                    progress.update(task, description=f"Updated {len(courts)} courts")

                    # Save data if requested
                    if save_data:
                        try:
                            timestamp = datetime.now().strftime("%H%M%S")
                            html_path = save_html_data(
                                html_content, f"_watch_{timestamp}"
                            )
                            json_path = save_json_data(
                                courts,
                                f"_watch_{timestamp}",
                                scraper.get_last_request_url(),
                            )
                            logger.info(
                                f"Watch data saved - HTML: {html_path}, JSON: {json_path}"
                            )
                        except Exception as e:
                            logger.error(f"Error saving watch data: {e}")
                else:
                    logger.error("No courts could be retrieved during watch update")
                    progress.update(task, description="Failed to fetch court data")

            # Display current data
            courts = db.get_courts(
                sport_type=sport.title() if sport else None, date=parsed_date
            )

            logger.debug(f"Displaying {len(courts)} courts in watch mode")

            if courts:
                display_courts_table(courts)
            else:
                console.print("[yellow]No court data available.[/yellow]")
                console.print(
                    "[dim]The website may be blocking requests. Try stopping and restarting.[/dim]"
                )

            console.print(f"\n[dim]Next update in {interval} seconds...[/dim]")
            logger.debug(f"Waiting {interval} seconds before next update")
            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Watch mode stopped by user")
        console.print("\n[yellow]Monitoring stopped.[/yellow]")
