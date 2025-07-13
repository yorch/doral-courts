"""Stats command implementation."""

import click
from rich.console import Console
from rich.panel import Panel

from ...core.database import Database
from ...utils.logger import get_logger

logger = get_logger(__name__)
console = Console()


@click.command()
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
    stats_data = db.get_stats()

    logger.debug(f"Database stats: {stats_data}")

    if stats_data["total_courts"] == 0:
        logger.warning("No data available in database")
        console.print("[yellow]No court data available in database.[/yellow]")
        console.print("[blue]Try running: doral-courts list[/blue]")
        console.print(
            "[dim]Note: The website may be blocking automated requests.[/dim]"
        )
        return

    logger.info(f"Displaying statistics for {stats_data['total_courts']} courts")

    # Create stats panel
    stats_text = f"""
Total Courts: {stats_data['total_courts']}
Last Updated: {stats_data['last_updated'] or 'Never'}

Sport Breakdown:
"""

    for sport, count in stats_data["sport_counts"].items():
        stats_text += f"  {sport}: {count}\n"

    stats_text += "\nAvailability Status:\n"
    for status, count in stats_data["availability_counts"].items():
        stats_text += f"  {status}: {count}\n"

    panel = Panel(
        stats_text.strip(), title="Doral Courts Statistics", border_style="blue"
    )
    console.print(panel)
