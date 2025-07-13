"""Slots command implementation."""

from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ...core.database import Database
from ...core.scraper import Scraper
from ...utils.date_utils import parse_date_input
from ...utils.file_utils import save_html_data, save_json_data
from ...utils.logger import get_logger

logger = get_logger(__name__)
console = Console()


@click.command()
@click.option("--court", help="Show detailed time slots for a specific court")
@click.option(
    "--date",
    help="Date to check (default: today). Supports MM/DD/YYYY, today, tomorrow, yesterday, +N, -N",
)
@click.option("--available-only", is_flag=True, help="Show only available time slots")
@click.pass_context
def slots(ctx, court: Optional[str], date: Optional[str], available_only: bool):
    """Show detailed time slot availability for courts. Always fetches fresh data."""
    # Parse date input
    try:
        parsed_date = parse_date_input(date)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    logger.info("Starting detailed time slots display - fetching fresh data")
    logger.debug(
        f"Filters - Court: {court}, Date: {date} -> {parsed_date}, Available only: {available_only}"
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
            courts, html_content = scraper.fetch_courts_with_html(date=parsed_date)
        else:
            courts = scraper.fetch_courts(date=parsed_date)
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
                    html_path = save_html_data(html_content, "_slots")
                    json_path = save_json_data(
                        courts, "_slots", scraper.get_last_request_url()
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

    # Apply court filter to fresh data
    if court:
        courts = [c for c in courts if court.lower() in c.name.lower()]
        if not courts:
            console.print(f"[red]No courts found matching '{court}'[/red]")
            return

    if not courts:
        console.print("[red]No courts found matching your criteria.[/red]")
        return

    for court_obj in courts:
        if not court_obj.time_slots:
            console.print(
                f"\n[yellow]{court_obj.name} - No time slots available[/yellow]"
            )
            continue

        # Filter slots if needed
        slots_to_show = court_obj.time_slots
        if available_only:
            slots_to_show = [
                slot for slot in court_obj.time_slots if slot.status == "Available"
            ]

        if not slots_to_show and available_only:
            console.print(
                f"\n[yellow]{court_obj.name} - No available time slots[/yellow]"
            )
            continue

        # Create table for this court's time slots
        table = Table(title=f"{court_obj.name} - {court_obj.date}")
        table.add_column("Start Time", style="cyan")
        table.add_column("End Time", style="cyan")
        table.add_column("Status", style="bold")

        for slot in slots_to_show:
            # Color code the status
            if slot.status == "Available":
                status_style = "[green]"
            else:
                status_style = "[red]"

            table.add_row(
                slot.start_time, slot.end_time, f"{status_style}{slot.status}[/]"
            )

        console.print(table)
