"""Cleanup command implementation."""

import click
from rich.console import Console

from ...core.database import Database
from ...utils.logger import get_logger

logger = get_logger(__name__)
console = Console()


@click.command()
@click.option("--days", default=7, help="Remove data older than N days")
@click.pass_context
def cleanup(ctx, days: int):
    """Clean up old court data."""
    logger.info(f"Starting cleanup of data older than {days} days")

    db = Database()

    # Get count before cleanup for logging
    stats_before = db.get_stats()
    total_before = stats_before["total_courts"]
    logger.debug(f"Total courts before cleanup: {total_before}")

    db.clear_old_data(days)

    # Get count after cleanup
    stats_after = db.get_stats()
    total_after = stats_after["total_courts"]
    removed_count = total_before - total_after

    logger.info(f"Cleanup completed. Removed {removed_count} old records")
    logger.debug(f"Courts remaining: {total_after}")

    console.print(
        f"[green]Cleaned up data older than {days} days. Removed {removed_count} records.[/green]"
    )
