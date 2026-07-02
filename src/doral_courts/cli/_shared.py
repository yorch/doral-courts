"""Shared helpers for CLI commands."""

from typing import List, Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.database import Database
from ..core.html_extractor import Court
from ..core.scraper import Scraper
from ..utils.file_utils import save_html_data, save_json_data
from ..utils.logger import get_logger

logger = get_logger(__name__)
console = Console()


def fetch_and_store(
    ctx: click.Context,
    parsed_date: str,
    *,
    sport: Optional[str] = None,
    suffix: str = "",
    db: Optional[Database] = None,
    description: str = "Fetching court data...",
) -> tuple[List[Court], str]:
    """Fetch fresh court data, persist it, and optionally save it to disk.

    Consolidates the fetch -> store -> (optional) save-to-disk workflow that
    is shared by every data-fetching command. On a successful fetch the data
    is inserted into the database for historical tracking; when the global
    ``--save-data`` flag is set the raw HTML and JSON are also written to the
    ``data/`` directory.

    Args:
        ctx: Click context (provides the global ``save_data`` flag).
        parsed_date: Date in MM/DD/YYYY format (already validated).
        sport: Optional sport filter passed to the scraper.
        suffix: Filename suffix used when saving HTML/JSON (e.g. ``"_list"``).
        db: Optional database instance (defaults to a new ``Database()``).
        description: Spinner description shown while fetching.

    Returns:
        A ``(courts, source_url)`` tuple. ``courts`` is empty if the fetch
        failed, in which case a user-facing error has already been printed.
    """
    db = db or Database()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(description, total=None)

        scraper = Scraper()
        save_data = ctx.obj.get("save_data", False)

        if save_data:
            courts, html_content = scraper.fetch_courts_with_html(
                date=parsed_date, sport_filter=sport
            )
        else:
            courts = scraper.fetch_courts(date=parsed_date, sport_filter=sport)
            html_content = ""

        source_url = scraper.get_last_request_url()

        if not courts:
            logger.error("No court data could be retrieved from website")
            console.print("[red]Unable to fetch court data from website.[/red]")
            console.print(
                "[yellow]The website may be temporarily"
                " unavailable or blocking requests.[/yellow]"
            )
            return [], source_url

        logger.info("Successfully fetched %d courts from website", len(courts))
        inserted_count = db.insert_courts(courts)
        logger.debug(
            "Inserted/updated %d courts in database for tracking", inserted_count
        )
        progress.update(task, description=f"Fetched {len(courts)} courts")

        if save_data:
            try:
                html_path = save_html_data(html_content, suffix)
                json_path = save_json_data(courts, suffix, source_url)
                console.print("[green]Data saved to:[/green]")
                console.print(f"  HTML: {html_path}")
                console.print(f"  JSON: {json_path}")
            except Exception as e:
                logger.error("Error saving data: %s", e)
                console.print(f"[red]Error saving data: {e}[/red]")

    return courts, source_url
