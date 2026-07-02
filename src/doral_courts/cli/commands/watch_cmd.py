"""Watch command implementation."""

import time
from datetime import datetime
from typing import Optional

import click
from rich.console import Console

from ...core.database import Database
from ...display.tables import display_courts_table
from ...utils.date_utils import parse_date_input
from ...utils.logger import get_logger
from .._shared import fetch_and_store

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
    help=(
        "Date to monitor (default: today). "
        "Supports MM/DD/YYYY, today, tomorrow, yesterday, +N, -N"
    ),
)
@click.pass_context
def watch(
    ctx: click.Context,
    interval: int,
    sport: Optional[str],
    date: Optional[str],
) -> None:
    """Monitor court availability with real-time updates."""
    # Parse date input
    try:
        parsed_date = parse_date_input(date)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    logger.info("Starting watch mode with %ss interval", interval)
    logger.debug("Watch filters - Sport: %s, Date: %s -> %s", sport, date, parsed_date)

    console.print(
        f"[blue]Monitoring court availability every "
        f"{interval} seconds. Press Ctrl+C to stop.[/blue]"
    )

    update_count = 0
    try:
        while True:
            update_count += 1
            logger.debug("Watch update #%s", update_count)

            console.clear()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            console.print(f"[bold]Last updated: {now_str}[/bold]\n")

            db = Database()

            # Fetch fresh data, store it, and optionally save it to disk.
            timestamp = datetime.now().strftime("%H%M%S")
            logger.debug("Fetching fresh court data for watch update")
            fetch_and_store(
                ctx,
                parsed_date,
                sport=sport,
                suffix=f"_watch_{timestamp}",
                db=db,
                description="Fetching latest data...",
            )

            # Display current data from the database
            courts = db.get_courts(
                sport_type=sport.title() if sport else None, date=parsed_date
            )

            logger.debug("Displaying %s courts in watch mode", len(courts))

            if courts:
                display_courts_table(courts)
            else:
                console.print("[yellow]No court data available.[/yellow]")
                console.print(
                    "[dim]The website may be blocking "
                    "requests. Try stopping and "
                    "restarting.[/dim]"
                )

            console.print(f"\n[dim]Next update in {interval} seconds...[/dim]")
            logger.debug("Waiting %s seconds before next update", interval)
            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Watch mode stopped by user")
        console.print("\n[yellow]Monitoring stopped.[/yellow]")
