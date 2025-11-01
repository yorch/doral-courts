"""Monitor command for continuous background polling."""

import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Optional

import click
from rich.console import Console

from ...core.database import Database
from ...core.scraper import Scraper
from ...utils.date_utils import parse_date_input
from ...utils.logger import get_logger

logger = get_logger(__name__)
console = Console()

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    shutdown_requested = True
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")


@click.command()
@click.option(
    "--interval",
    default=10,
    help="Polling interval in minutes (default: 10 minutes)",
    type=int,
)
@click.option(
    "--sport",
    type=click.Choice(["tennis", "pickleball"], case_sensitive=False),
    help="Filter by sport type (default: monitor both)",
)
@click.option(
    "--location",
    help="Filter by location (e.g., 'Doral Central Park')",
)
@click.option(
    "--days-ahead",
    default=2,
    help="Number of days ahead to monitor (default: 2 - today and tomorrow)",
    type=int,
)
@click.option(
    "--quiet",
    is_flag=True,
    help="Suppress console output (logs only)",
)
@click.pass_context
def monitor(
    ctx,
    interval: int,
    sport: Optional[str],
    location: Optional[str],
    days_ahead: int,
    quiet: bool,
):
    """Run continuous background monitoring of court availability.

    This command polls the court reservation system at regular intervals and
    stores historical availability data. Useful for analyzing booking patterns
    and tracking how quickly courts get reserved.

    Examples:
        # Monitor all courts every 10 minutes
        doral-courts monitor

        # Monitor pickleball only every 5 minutes
        doral-courts monitor --sport pickleball --interval 5

        # Monitor next 3 days, quietly
        doral-courts monitor --days-ahead 3 --quiet

        # Monitor specific location
        doral-courts monitor --location "Doral Legacy Park"
    """
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Convert interval from minutes to seconds
    interval_seconds = interval * 60

    # Build filter description
    filters = []
    if sport:
        filters.append(f"sport={sport}")
    if location:
        filters.append(f"location={location}")
    filter_str = ", ".join(filters) if filters else "all courts"

    # Start message
    start_msg = (
        f"🔄 Starting continuous monitoring\n"
        f"   Interval: {interval} minutes\n"
        f"   Filters: {filter_str}\n"
        f"   Days ahead: {days_ahead}\n"
        f"   Press Ctrl+C to stop gracefully"
    )

    if not quiet:
        console.print(f"[blue]{start_msg}[/blue]")

    logger.info(f"Monitor started - {filter_str}, interval={interval}min, days={days_ahead}")

    db = Database()
    scraper = Scraper()
    poll_count = 0
    total_courts_saved = 0

    try:
        while not shutdown_requested:
            poll_count += 1
            poll_start = datetime.now()

            logger.info(f"Poll #{poll_count} starting at {poll_start.strftime('%Y-%m-%d %H:%M:%S')}")

            if not quiet:
                console.print(
                    f"\n[dim]Poll #{poll_count} - {poll_start.strftime('%H:%M:%S')}[/dim]"
                )

            # Calculate dates to monitor
            dates_to_monitor = []
            for day_offset in range(days_ahead):
                target_date = datetime.now() + timedelta(days=day_offset)
                dates_to_monitor.append(target_date.strftime("%m/%d/%Y"))

            # Fetch data for each date
            courts_this_poll = 0
            for target_date in dates_to_monitor:
                try:
                    logger.debug(f"Fetching courts for {target_date}, sport={sport}")

                    courts = scraper.fetch_courts(
                        date=target_date, sport_filter=sport
                    )

                    # Filter by location if specified
                    if location and courts:
                        courts = [c for c in courts if location.lower() in c.location.lower()]

                    if courts:
                        inserted = db.insert_courts(courts)
                        courts_this_poll += len(courts)
                        total_courts_saved += inserted

                        logger.info(
                            f"  {target_date}: {len(courts)} courts fetched, {inserted} saved"
                        )

                        if not quiet:
                            console.print(
                                f"  [green]✓[/green] {target_date}: {len(courts)} courts, {inserted} saved"
                            )
                    else:
                        logger.warning(f"  {target_date}: No courts retrieved")
                        if not quiet:
                            console.print(f"  [yellow]⚠[/yellow] {target_date}: No data")

                except Exception as e:
                    logger.error(f"Error fetching {target_date}: {e}", exc_info=True)
                    if not quiet:
                        console.print(f"  [red]✗[/red] {target_date}: Error - {e}")

            # Poll summary
            poll_duration = (datetime.now() - poll_start).total_seconds()
            logger.info(
                f"Poll #{poll_count} complete - {courts_this_poll} courts in {poll_duration:.1f}s"
            )

            if not quiet:
                console.print(
                    f"[dim]  Total this session: {total_courts_saved} records saved, "
                    f"{poll_count} polls completed[/dim]"
                )

            # Sleep until next poll (unless shutdown requested)
            if not shutdown_requested:
                next_poll = poll_start + timedelta(seconds=interval_seconds)
                sleep_time = (next_poll - datetime.now()).total_seconds()

                if sleep_time > 0:
                    logger.debug(f"Sleeping for {sleep_time:.0f} seconds until next poll")
                    if not quiet:
                        next_time = next_poll.strftime("%H:%M:%S")
                        console.print(f"[dim]  Next poll at {next_time}...[/dim]")

                    # Sleep in small chunks to respond quickly to shutdown
                    while sleep_time > 0 and not shutdown_requested:
                        time.sleep(min(1, sleep_time))
                        sleep_time -= 1
                else:
                    logger.warning(
                        f"Poll took longer than interval ({poll_duration:.1f}s > {interval_seconds}s)"
                    )

    except KeyboardInterrupt:
        logger.info("Monitor interrupted by user (Ctrl+C)")
        if not quiet:
            console.print("\n[yellow]Monitoring interrupted...[/yellow]")

    except Exception as e:
        logger.error(f"Monitor error: {e}", exc_info=True)
        if not quiet:
            console.print(f"\n[red]Monitor error: {e}[/red]")
        sys.exit(1)

    finally:
        # Shutdown summary
        summary_msg = (
            f"\n📊 Monitoring Summary:\n"
            f"   Total polls: {poll_count}\n"
            f"   Records saved: {total_courts_saved}\n"
            f"   Duration: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if not quiet:
            console.print(f"[blue]{summary_msg}[/blue]")

        logger.info(f"Monitor stopped - {poll_count} polls, {total_courts_saved} records saved")
        logger.info("Monitor shutdown complete")
