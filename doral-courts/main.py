import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime
from scraper import DoralCourtsScraper, Court
from database import DoralCourtsDB
from logger import setup_logging, get_logger
from typing import List, Optional

console = Console()
logger = get_logger(__name__)

@click.group()
@click.version_option(version="0.1.0")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """Doral Courts CLI - Display tennis and pickleball court availability."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    setup_logging(verbose=verbose)

@cli.command()
@click.option('--sport', type=click.Choice(['tennis', 'pickleball'], case_sensitive=False), 
              help='Filter by sport type')
@click.option('--status', type=click.Choice(['available', 'booked', 'maintenance'], case_sensitive=False),
              help='Filter by availability status')
@click.option('--date', help='Date to check (MM/DD/YYYY format)')
@click.option('--refresh', is_flag=True, help='Fetch fresh data from website')
@click.pass_context
def list(ctx, sport: Optional[str], status: Optional[str], date: Optional[str], refresh: bool):
    """List available courts with optional filters."""
    verbose = ctx.obj.get('verbose', False)
    
    logger.info("Starting court listing command")
    logger.debug(f"Filters - Sport: {sport}, Status: {status}, Date: {date}, Refresh: {refresh}")
    
    db = DoralCourtsDB()
    
    # Check if we need to fetch fresh data
    existing_courts = db.get_courts()
    logger.debug(f"Found {len(existing_courts)} existing courts in database")
    
    if refresh or not existing_courts:
        logger.info("Fetching fresh data from website")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching court data...", total=None)
            
            scraper = DoralCourtsScraper()
            courts = scraper.fetch_courts(date=date, sport_filter=sport)
            
            if courts:
                logger.info(f"Successfully fetched {len(courts)} courts from website")
                inserted_count = db.insert_courts(courts)
                logger.debug(f"Inserted/updated {inserted_count} courts in database")
                progress.update(task, description=f"Fetched {len(courts)} courts")
            else:
                logger.warning("No court data found from website")
                console.print("[yellow]No court data found. Using cached data if available.[/yellow]")
    else:
        logger.info("Using existing data from database")
    
    # Get courts from database with filters
    logger.debug("Applying filters and retrieving courts from database")
    courts = db.get_courts(
        sport_type=sport.title() if sport else None,
        availability_status=status.title() if status else None,
        date=date
    )
    
    logger.info(f"Found {len(courts)} courts matching criteria")
    
    if not courts:
        console.print("[red]No courts found matching your criteria.[/red]")
        return
    
    # Display courts in a table
    logger.debug("Displaying courts table")
    display_courts_table(courts)

@cli.command()
@click.pass_context
def stats(ctx):
    """Show database statistics."""
    logger.info("Generating database statistics")
    
    db = DoralCourtsDB()
    stats = db.get_stats()
    
    logger.debug(f"Database stats: {stats}")
    
    if stats['total_courts'] == 0:
        logger.warning("No data available in database")
        console.print("[yellow]No data available. Use 'doral-courts list --refresh' to fetch data.[/yellow]")
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
@click.option('--days', default=7, help='Remove data older than N days')
@click.pass_context
def cleanup(ctx, days: int):
    """Clean up old court data."""
    logger.info(f"Starting cleanup of data older than {days} days")
    
    db = DoralCourtsDB()
    
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
@click.option('--interval', default=300, help='Update interval in seconds (default: 5 minutes)')
@click.option('--sport', type=click.Choice(['tennis', 'pickleball'], case_sensitive=False), 
              help='Filter by sport type')
@click.option('--date', help='Date to monitor (MM/DD/YYYY format)')
@click.pass_context
def watch(ctx, interval: int, sport: Optional[str], date: Optional[str]):
    """Monitor court availability with real-time updates."""
    import time
    
    logger.info(f"Starting watch mode with {interval}s interval")
    logger.debug(f"Watch filters - Sport: {sport}, Date: {date}")
    
    console.print(f"[blue]Monitoring court availability every {interval} seconds. Press Ctrl+C to stop.[/blue]")
    
    update_count = 0
    try:
        while True:
            update_count += 1
            logger.debug(f"Watch update #{update_count}")
            
            console.clear()
            console.print(f"[bold]Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/bold]\n")
            
            db = DoralCourtsDB()
            scraper = DoralCourtsScraper()
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Fetching latest data...", total=None)
                
                logger.debug("Fetching fresh court data for watch update")
                courts = scraper.fetch_courts(date=date, sport_filter=sport)
                
                if courts:
                    logger.debug(f"Fetched {len(courts)} courts for watch update")
                    inserted_count = db.insert_courts(courts)
                    logger.debug(f"Updated {inserted_count} courts in database")
                    progress.update(task, description=f"Updated {len(courts)} courts")
                else:
                    logger.warning("No courts found during watch update")
            
            # Display current data
            courts = db.get_courts(
                sport_type=sport.title() if sport else None,
                date=date
            )
            
            logger.debug(f"Displaying {len(courts)} courts in watch mode")
            
            if courts:
                display_courts_table(courts)
            else:
                console.print("[yellow]No courts found.[/yellow]")
            
            console.print(f"\n[dim]Next update in {interval} seconds...[/dim]")
            logger.debug(f"Waiting {interval} seconds before next update")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logger.info("Watch mode stopped by user")
        console.print("\n[yellow]Monitoring stopped.[/yellow]")

def display_courts_table(courts: List[Court]):
    """Display courts in a formatted table."""
    table = Table(title="Doral Courts Availability")
    
    table.add_column("Court Name", style="cyan", no_wrap=True)
    table.add_column("Sport", style="magenta")
    table.add_column("Date", style="green")
    table.add_column("Time", style="yellow")
    table.add_column("Status", style="bold")
    table.add_column("Surface", style="blue")
    table.add_column("Price", style="green")
    
    for court in courts:
        # Color code the status
        if "available" in court.availability_status.lower():
            status_style = "[green]"
        elif "booked" in court.availability_status.lower():
            status_style = "[red]"
        else:
            status_style = "[yellow]"
        
        table.add_row(
            court.name,
            court.sport_type,
            court.date,
            court.time_slot,
            f"{status_style}{court.availability_status}[/]",
            court.surface_type,
            court.price or "N/A"
        )
    
    console.print(table)

if __name__ == "__main__":
    cli()
