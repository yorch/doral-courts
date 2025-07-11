import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime
from scraper import DoralCourtsScraper, Court
from database import DoralCourtsDB
from typing import List, Optional

console = Console()

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Doral Courts CLI - Display tennis and pickleball court availability."""
    pass

@cli.command()
@click.option('--sport', type=click.Choice(['tennis', 'pickleball'], case_sensitive=False), 
              help='Filter by sport type')
@click.option('--status', type=click.Choice(['available', 'booked', 'maintenance'], case_sensitive=False),
              help='Filter by availability status')
@click.option('--date', help='Date to check (MM/DD/YYYY format)')
@click.option('--refresh', is_flag=True, help='Fetch fresh data from website')
def list(sport: Optional[str], status: Optional[str], date: Optional[str], refresh: bool):
    """List available courts with optional filters."""
    
    db = DoralCourtsDB()
    
    if refresh or not db.get_courts():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching court data...", total=None)
            
            scraper = DoralCourtsScraper()
            courts = scraper.fetch_courts(date=date, sport_filter=sport)
            
            if courts:
                db.insert_courts(courts)
                progress.update(task, description=f"Fetched {len(courts)} courts")
            else:
                console.print("[yellow]No court data found. Using cached data if available.[/yellow]")
    
    # Get courts from database with filters
    courts = db.get_courts(
        sport_type=sport.title() if sport else None,
        availability_status=status.title() if status else None,
        date=date
    )
    
    if not courts:
        console.print("[red]No courts found matching your criteria.[/red]")
        return
    
    # Display courts in a table
    display_courts_table(courts)

@cli.command()
def stats():
    """Show database statistics."""
    db = DoralCourtsDB()
    stats = db.get_stats()
    
    if stats['total_courts'] == 0:
        console.print("[yellow]No data available. Use 'doral-courts list --refresh' to fetch data.[/yellow]")
        return
    
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
def cleanup(days: int):
    """Clean up old court data."""
    db = DoralCourtsDB()
    db.clear_old_data(days)
    console.print(f"[green]Cleaned up data older than {days} days.[/green]")

@cli.command()
@click.option('--interval', default=300, help='Update interval in seconds (default: 5 minutes)')
@click.option('--sport', type=click.Choice(['tennis', 'pickleball'], case_sensitive=False), 
              help='Filter by sport type')
@click.option('--date', help='Date to monitor (MM/DD/YYYY format)')
def watch(interval: int, sport: Optional[str], date: Optional[str]):
    """Monitor court availability with real-time updates."""
    import time
    
    console.print(f"[blue]Monitoring court availability every {interval} seconds. Press Ctrl+C to stop.[/blue]")
    
    try:
        while True:
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
                courts = scraper.fetch_courts(date=date, sport_filter=sport)
                
                if courts:
                    db.insert_courts(courts)
                    progress.update(task, description=f"Updated {len(courts)} courts")
            
            # Display current data
            courts = db.get_courts(
                sport_type=sport.title() if sport else None,
                date=date
            )
            
            if courts:
                display_courts_table(courts)
            else:
                console.print("[yellow]No courts found.[/yellow]")
            
            console.print(f"\n[dim]Next update in {interval} seconds...[/dim]")
            time.sleep(interval)
            
    except KeyboardInterrupt:
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
