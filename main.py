#!/usr/bin/env python3
"""
Doral Courts CLI - Command-line interface for checking tennis and pickleball court availability.

MIT License
Copyright (c) 2025 Jorge Barnaby
"""

import click
import os
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from datetime import datetime
from scraper import Scraper
from html_extractor import Court, TimeSlot
from database import Database
from logger import setup_logging, get_logger
from utils import save_html_data, save_json_data, display_courts_table, display_detailed_court_data, display_time_slots_summary, display_available_slots_table, parse_date_input, display_courts_list, display_locations_list
from typing import List, Optional

console = Console()
logger = get_logger(__name__)


@click.group()
@click.version_option(version="0.1.0")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--save-data', is_flag=True, help='Save retrieved HTML and JSON data to files')
@click.pass_context
def cli(ctx, verbose, save_data):
    """
    Doral Courts CLI - Display tennis and pickleball court availability.

    Main entry point for the command-line interface. Sets up global configuration
    including logging verbosity and data saving preferences.

    Args:
        ctx: Click context object for sharing data between commands
        verbose: Enable detailed logging output
        save_data: Save HTML and JSON data to files for analysis

    Global Options:
        --verbose, -v: Enable verbose logging for debugging
        --save-data: Export scraped data to data/ directory
        --version: Show version and exit
        --help: Show help message

    Examples:
        doral-courts --verbose list
        doral-courts --save-data list-available-slots --date tomorrow
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['save_data'] = save_data
    setup_logging(verbose=verbose)

@cli.command()
@click.option('--sport', type=click.Choice(['tennis', 'pickleball'], case_sensitive=False),
              help='Filter by sport type')
@click.option('--status', type=click.Choice(['available', 'booked', 'maintenance'], case_sensitive=False),
              help='Filter by availability status')
@click.option('--date', help='Date to check (default: today). Supports MM/DD/YYYY, today, tomorrow, yesterday, +N, -N')
@click.pass_context
def list(ctx, sport: Optional[str], status: Optional[str], date: Optional[str]):
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
    verbose = ctx.obj.get('verbose', False)

    # Parse date input
    try:
        parsed_date = parse_date_input(date)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    logger.info("Starting court listing command - fetching fresh data")
    logger.debug(f"Filters - Sport: {sport}, Status: {status}, Date: {date} -> {parsed_date}")

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
        save_data = ctx.obj.get('save_data', False)
        if save_data:
            courts, html_content = scraper.fetch_courts_with_html(date=date, sport_filter=sport)
        else:
            courts = scraper.fetch_courts(date=date, sport_filter=sport)
            html_content = ""

        if courts:
            logger.info(f"Successfully fetched {len(courts)} courts from website")
            # Store in database for historical tracking
            inserted_count = db.insert_courts(courts)
            logger.debug(f"Inserted/updated {inserted_count} courts in database for tracking")
            progress.update(task, description=f"Fetched {len(courts)} courts")

            # Save data if requested
            if save_data:
                try:
                    html_path = save_html_data(html_content, "_list")
                    json_path = save_json_data(courts, "_list", scraper.get_last_request_url())
                    console.print(f"[green]Data saved to:[/green]")
                    console.print(f"  HTML: {html_path}")
                    console.print(f"  JSON: {json_path}")
                except Exception as e:
                    logger.error(f"Error saving data: {e}")
                    console.print(f"[red]Error saving data: {e}[/red]")
        else:
            logger.error("No court data could be retrieved from website")
            console.print("[red]Unable to fetch court data from website.[/red]")
            console.print("[yellow]The website may be temporarily unavailable or blocking requests.[/yellow]")
            return

    # Apply filters to fresh data
    logger.debug("Applying filters to fresh data")
    filtered_courts = courts

    if sport:
        filtered_courts = [court for court in filtered_courts if court.sport_type.lower() == sport.lower()]
        logger.debug(f"Applied sport filter '{sport}': {len(courts)} -> {len(filtered_courts)} courts")

    if status:
        filtered_courts = [court for court in filtered_courts if status.lower() in court.availability_status.lower()]
        logger.debug(f"Applied status filter '{status}': {len(filtered_courts)} courts")

    logger.info(f"Found {len(filtered_courts)} courts matching criteria")

    if not filtered_courts:
        console.print("[red]No courts found matching your criteria.[/red]")
        return

    # Display courts in a table
    logger.debug("Displaying courts table")
    display_courts_table(filtered_courts)

@cli.command()
@click.pass_context
def stats(ctx):
    """
    Show database statistics.

    Displays comprehensive statistics about the local SQLite database including
    total courts, last update time, and breakdown by sport and availability status.
    Uses only cached data from the database.

    Args:
        ctx: Click context (unused but required by Click)

    Output:
        Rich panel displaying:
        - Total Courts: Number of court records in database
        - Last Updated: Most recent data fetch timestamp
        - Sport Breakdown: Count of tennis vs pickleball courts
        - Availability Status: Count by availability status

    Examples:
        doral-courts stats

    Note:
        Shows historical database content only. Does not fetch fresh data.
        If database is empty, suggests running 'list' command first.
    """
    logger.info("Generating database statistics")

    db = Database()
    stats = db.get_stats()

    logger.debug(f"Database stats: {stats}")

    if stats['total_courts'] == 0:
        logger.warning("No data available in database")
        console.print("[yellow]No court data available in database.[/yellow]")
        console.print("[blue]Try running: doral-courts list --refresh[/blue]")
        console.print("[dim]Note: The website may be blocking automated requests.[/dim]")
        return

    logger.info(f"Displaying statistics for {stats['total_courts']} courts")

    # Create stats panel
    stats_text = f"""
Total Courts: {stats['total_courts']}
Last Updated: {stats['last_updated'] or 'Never'}

Sport Breakdown:
"""

    for sport, count in stats['sport_counts'].items():
        stats_text += f"  {sport}: {count}\n"

    stats_text += "\nAvailability Status:\n"
    for status, count in stats['availability_counts'].items():
        stats_text += f"  {status}: {count}\n"

    panel = Panel(stats_text.strip(), title="Doral Courts Statistics", border_style="blue")
    console.print(panel)

@cli.command()
@click.option('--court', help='Show detailed time slots for a specific court')
@click.option('--date', help='Date to check (default: today). Supports MM/DD/YYYY, today, tomorrow, yesterday, +N, -N')
@click.option('--available-only', is_flag=True, help='Show only available time slots')
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
    logger.debug(f"Filters - Court: {court}, Date: {date} -> {parsed_date}, Available only: {available_only}")

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
        save_data = ctx.obj.get('save_data', False)
        if save_data:
            courts, html_content = scraper.fetch_courts_with_html(date=parsed_date)
        else:
            courts = scraper.fetch_courts(date=parsed_date)
            html_content = ""

        if courts:
            logger.info(f"Successfully fetched {len(courts)} courts from website")
            # Store in database for historical tracking
            inserted_count = db.insert_courts(courts)
            logger.debug(f"Inserted/updated {inserted_count} courts in database for tracking")
            progress.update(task, description=f"Fetched {len(courts)} courts")

            # Save data if requested
            if save_data:
                try:
                    html_path = save_html_data(html_content, "_slots")
                    json_path = save_json_data(courts, "_slots", scraper.get_last_request_url())
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
            console.print(f"\n[yellow]{court_obj.name} - No time slots available[/yellow]")
            continue

        # Filter slots if needed
        slots_to_show = court_obj.time_slots
        if available_only:
            slots_to_show = [slot for slot in court_obj.time_slots if slot.status == "Available"]

        if not slots_to_show and available_only:
            console.print(f"\n[yellow]{court_obj.name} - No available time slots[/yellow]")
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
                slot.start_time,
                slot.end_time,
                f"{status_style}{slot.status}[/]"
            )

        console.print(table)

@cli.command()
@click.option('--mode', type=click.Choice(['detailed', 'summary'], case_sensitive=False),
              default='detailed', help='Display mode: detailed (full court info) or summary (time slots analysis)')
@click.option('--sport', type=click.Choice(['tennis', 'pickleball'], case_sensitive=False),
              help='Filter by sport type')
@click.option('--date', help='Date to check (default: today). Supports MM/DD/YYYY, today, tomorrow, yesterday, +N, -N')
@click.pass_context
def data(ctx, mode: str, sport: Optional[str], date: Optional[str]):
    """Display comprehensive view of all scraped data from the website. Always fetches fresh data."""
    # Parse date input
    try:
        parsed_date = parse_date_input(date)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    logger.info("Starting comprehensive data display - fetching fresh data")
    logger.debug(f"Mode: {mode}, Sport: {sport}, Date: {date} -> {parsed_date}")

    db = Database()

    # Initialize scraper and always fetch fresh data
    scraper = Scraper()

    logger.info("Fetching fresh data from website")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching latest data...", total=None)

        # Check if we should save data
        save_data = ctx.obj.get('save_data', False)
        if save_data:
            courts, html_content = scraper.fetch_courts_with_html(date=parsed_date, sport_filter=sport)
        else:
            courts = scraper.fetch_courts(date=parsed_date, sport_filter=sport)
            html_content = ""

        # Get the actual URL used for the request
        actual_url = scraper.get_last_request_url()

        if courts:
            logger.info(f"Successfully fetched {len(courts)} courts from website")
            # Store in database for historical tracking
            inserted_count = db.insert_courts(courts)
            logger.debug(f"Inserted/updated {inserted_count} courts in database for tracking")
            progress.update(task, description=f"Fetched {len(courts)} courts")

            # Save data if requested
            if save_data:
                try:
                    html_path = save_html_data(html_content, "_data")
                    json_path = save_json_data(courts, "_data", actual_url)
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
        filtered_courts = [court for court in filtered_courts if court.sport_type.lower() == sport.lower()]
        logger.debug(f"Applied sport filter '{sport}': {len(courts)} -> {len(filtered_courts)} courts")

    logger.info(f"Found {len(filtered_courts)} courts for comprehensive display")

    if not filtered_courts:
        console.print("[red]No courts found matching your criteria.[/red]")
        return

    # Display data based on mode
    if mode == 'detailed':
        display_detailed_court_data(filtered_courts, actual_url)
    else:  # summary mode
        display_time_slots_summary(filtered_courts, actual_url)

@cli.command()
@click.option('--days', default=7, help='Remove data older than N days')
@click.pass_context
def cleanup(ctx, days: int):
    """Clean up old court data."""
    logger.info(f"Starting cleanup of data older than {days} days")

    db = Database()

    # Get count before cleanup for logging
    stats_before = db.get_stats()
    total_before = stats_before['total_courts']
    logger.debug(f"Total courts before cleanup: {total_before}")

    db.clear_old_data(days)

    # Get count after cleanup
    stats_after = db.get_stats()
    total_after = stats_after['total_courts']
    removed_count = total_before - total_after

    logger.info(f"Cleanup completed. Removed {removed_count} old records")
    logger.debug(f"Courts remaining: {total_after}")

    console.print(f"[green]Cleaned up data older than {days} days. Removed {removed_count} records.[/green]")

@cli.command()
@click.option('--sport', type=click.Choice(['tennis', 'pickleball'], case_sensitive=False),
              help='Filter by sport type')
@click.option('--status', type=click.Choice(['available', 'booked', 'maintenance'], case_sensitive=False),
              help='Filter by availability status')
@click.option('--date', help='Date to check (default: today). Supports MM/DD/YYYY, today, tomorrow, yesterday, +N, -N')
@click.option('--mode', type=click.Choice(['table', 'detailed', 'summary'], case_sensitive=False),
              default='table', help='Display mode: table (simple), detailed (full info), or summary (analysis)')
@click.pass_context
def history(ctx, sport: Optional[str], status: Optional[str], date: Optional[str], mode: str):
    """View historical court data from database (cached data)."""
    # Parse date input
    try:
        parsed_date = parse_date_input(date)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    logger.info("Starting historical data display from database")
    logger.debug(f"Filters - Sport: {sport}, Status: {status}, Date: {date} -> {parsed_date}, Mode: {mode}")

    db = Database()

    # Get courts from database with filters
    logger.debug("Retrieving historical data from database")
    courts = db.get_courts(
        sport_type=sport.title() if sport else None,
        availability_status=status.title() if status else None,
        date=parsed_date
    )

    logger.info(f"Found {len(courts)} historical records matching criteria")

    if not courts:
        console.print("[red]No historical court data found matching your criteria.[/red]")
        console.print("[blue]Try running other commands to fetch fresh data first.[/blue]")
        return

    # Display historical data based on mode
    if mode == 'table':
        # Simple table display
        display_courts_table(courts)
    elif mode == 'detailed':
        # Detailed display with database note
        display_url = "Database (historical data)"
        display_detailed_court_data(courts, display_url)
    else:  # summary mode
        # Summary analysis with database note
        display_url = "Database (historical data)"
        display_time_slots_summary(courts, display_url)

@cli.command()
@click.option('--interval', default=300, help='Update interval in seconds (default: 5 minutes)')
@click.option('--sport', type=click.Choice(['tennis', 'pickleball'], case_sensitive=False),
              help='Filter by sport type')
@click.option('--date', help='Date to monitor (default: today). Supports MM/DD/YYYY, today, tomorrow, yesterday, +N, -N')
@click.pass_context
def watch(ctx, interval: int, sport: Optional[str], date: Optional[str]):
    """Monitor court availability with real-time updates."""
    import time

    # Parse date input
    try:
        parsed_date = parse_date_input(date)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    logger.info(f"Starting watch mode with {interval}s interval")
    logger.debug(f"Watch filters - Sport: {sport}, Date: {date} -> {parsed_date}")

    console.print(f"[blue]Monitoring court availability every {interval} seconds. Press Ctrl+C to stop.[/blue]")

    update_count = 0
    try:
        while True:
            update_count += 1
            logger.debug(f"Watch update #{update_count}")

            console.clear()
            console.print(f"[bold]Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/bold]\n")

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
                save_data = ctx.obj.get('save_data', False)
                if save_data:
                    courts, html_content = scraper.fetch_courts_with_html(date=parsed_date, sport_filter=sport)
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
                            html_path = save_html_data(html_content, f"_watch_{timestamp}")
                            json_path = save_json_data(courts, f"_watch_{timestamp}", scraper.get_last_request_url())
                            logger.info(f"Watch data saved - HTML: {html_path}, JSON: {json_path}")
                        except Exception as e:
                            logger.error(f"Error saving watch data: {e}")
                else:
                    logger.error("No courts could be retrieved during watch update")
                    progress.update(task, description="Failed to fetch court data")

            # Display current data
            courts = db.get_courts(
                sport_type=sport.title() if sport else None,
                date=parsed_date
            )

            logger.debug(f"Displaying {len(courts)} courts in watch mode")

            if courts:
                display_courts_table(courts)
            else:
                console.print("[yellow]No court data available.[/yellow]")
                console.print("[dim]The website may be blocking requests. Try stopping and restarting.[/dim]")

            console.print(f"\n[dim]Next update in {interval} seconds...[/dim]")
            logger.debug(f"Waiting {interval} seconds before next update")
            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Watch mode stopped by user")
        console.print("\n[yellow]Monitoring stopped.[/yellow]")

@cli.command(name='list-available-slots')
@click.option('--date', help='Date to check (default: today). Supports MM/DD/YYYY, today, tomorrow, yesterday, +N, -N')
@click.option('--sport', type=click.Choice(['tennis', 'pickleball'], case_sensitive=False),
              help='Filter by sport type')
@click.option('--location', help='Filter by location (e.g., "Doral Central Park")')
@click.pass_context
def list_available_slots(ctx, date: Optional[str], sport: Optional[str], location: Optional[str]):
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
        save_data = ctx.obj.get('save_data', False)
        if save_data:
            courts, html_content = scraper.fetch_courts_with_html(date=parsed_date, sport_filter=sport)
        else:
            courts = scraper.fetch_courts(date=parsed_date, sport_filter=sport)
            html_content = ""

        if courts:
            logger.info(f"Successfully fetched {len(courts)} courts from website")
            # Store in database for historical tracking
            inserted_count = db.insert_courts(courts)
            logger.debug(f"Inserted/updated {inserted_count} courts in database for tracking")
            progress.update(task, description=f"Fetched {len(courts)} courts")

            # Save data if requested
            if save_data:
                try:
                    html_path = save_html_data(html_content, "_available_slots")
                    json_path = save_json_data(courts, "_available_slots", scraper.get_last_request_url())
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
        filtered_courts = [court for court in filtered_courts if court.sport_type.lower() == sport.lower()]
        logger.debug(f"Applied sport filter '{sport}': {len(courts)} -> {len(filtered_courts)} courts")

    if location:
        filtered_courts = [court for court in filtered_courts if location.lower() in court.location.lower()]
        logger.debug(f"Applied location filter '{location}': {len(filtered_courts)} courts")

    logger.info(f"Found {len(filtered_courts)} courts for available slots display")

    if not filtered_courts:
        console.print("[red]No courts found matching your criteria.[/red]")
        return

    # Display available slots table
    display_available_slots_table(filtered_courts, parsed_date, scraper.get_last_request_url())

@cli.command(name='list-courts')
@click.option('--sport', type=click.Choice(['tennis', 'pickleball'], case_sensitive=False),
              help='Filter by sport type')
@click.option('--date', help='Date to check (default: today). Supports MM/DD/YYYY, today, tomorrow, yesterday, +N, -N')
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
        save_data = ctx.obj.get('save_data', False)
        if save_data:
            courts, html_content = scraper.fetch_courts_with_html(date=parsed_date, sport_filter=sport)
        else:
            courts = scraper.fetch_courts(date=parsed_date, sport_filter=sport)
            html_content = ""

        if courts:
            logger.info(f"Successfully fetched {len(courts)} courts from website")
            # Store in database for historical tracking
            inserted_count = db.insert_courts(courts)
            logger.debug(f"Inserted/updated {inserted_count} courts in database for tracking")
            progress.update(task, description=f"Fetched {len(courts)} courts")

            # Save data if requested
            if save_data:
                try:
                    html_path = save_html_data(html_content, "_list_courts")
                    json_path = save_json_data(courts, "_list_courts", scraper.get_last_request_url())
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

@cli.command(name='list-locations')
@click.option('--sport', type=click.Choice(['tennis', 'pickleball'], case_sensitive=False),
              help='Filter by sport type')
@click.option('--date', help='Date to check (default: today). Supports MM/DD/YYYY, today, tomorrow, yesterday, +N, -N')
@click.pass_context
def list_locations(ctx, sport: Optional[str], date: Optional[str]):
    """List all available locations with court counts."""
    # Parse date input
    try:
        parsed_date = parse_date_input(date)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    logger.info("Starting locations listing - fetching fresh data")
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
        save_data = ctx.obj.get('save_data', False)
        if save_data:
            courts, html_content = scraper.fetch_courts_with_html(date=parsed_date, sport_filter=sport)
        else:
            courts = scraper.fetch_courts(date=parsed_date, sport_filter=sport)
            html_content = ""

        if courts:
            logger.info(f"Successfully fetched {len(courts)} courts from website")
            # Store in database for historical tracking
            inserted_count = db.insert_courts(courts)
            logger.debug(f"Inserted/updated {inserted_count} courts in database for tracking")
            progress.update(task, description=f"Fetched {len(courts)} courts")

            # Save data if requested
            if save_data:
                try:
                    html_path = save_html_data(html_content, "_list_locations")
                    json_path = save_json_data(courts, "_list_locations", scraper.get_last_request_url())
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

    # Display locations list
    display_locations_list(courts, sport)


if __name__ == "__main__":
    cli()
