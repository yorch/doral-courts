"""Favorites command implementation."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...utils.config import Config
from ...utils.logger import get_logger

logger = get_logger(__name__)
console = Console()


@click.group()
def favorites():
    """
    Manage favorite courts.

    Save frequently accessed courts for quick reference. Favorite courts can be
    highlighted in listings and filtered for quick access.

    Commands:
        list   - Show all favorite courts
        add    - Add a court to favorites
        remove - Remove a court from favorites

    Examples:
        doral-courts favorites list
        doral-courts favorites add "DLP Tennis Court 1"
        doral-courts favorites remove "DLP Tennis Court 1"
    """
    pass


@favorites.command(name="list")
def list_favorites():
    """Show all favorite courts."""
    logger.info("Listing favorite courts")

    config = Config()
    favorite_courts = config.get_favorites()

    if not favorite_courts:
        console.print("[yellow]No favorite courts configured.[/yellow]")
        console.print(
            "[blue]Add favorites with: doral-courts favorites add <court_name>[/blue]"
        )
        return

    # Create table for favorites
    table = Table(title="⭐ Favorite Courts", show_header=True)
    table.add_column("#", style="dim")
    table.add_column("Court Name", style="cyan")

    for idx, court in enumerate(favorite_courts, 1):
        table.add_row(str(idx), court)

    console.print(table)
    console.print(f"\n[green]Total: {len(favorite_courts)} favorite courts[/green]")


@favorites.command(name="add")
@click.argument("court_name")
def add_favorite(court_name: str):
    """
    Add a court to favorites.

    Args:
        court_name: Name of the court to add (can be partial match)

    Examples:
        doral-courts favorites add "DLP Tennis Court 1"
        doral-courts favorites add "DLP Tennis Court 2"
    """
    logger.info(f"Adding court to favorites: {court_name}")

    config = Config()

    if config.add_favorite(court_name):
        console.print(f"[green]✅ Added '{court_name}' to favorites[/green]")

        # Show helpful tip
        panel = Panel(
            "[blue]Tip:[/blue] Use [yellow]doral-courts list --favorites[/yellow] to see only your favorite courts",
            title="Quick Access",
            border_style="blue",
        )
        console.print(panel)
    else:
        console.print(f"[yellow]'{court_name}' is already in favorites[/yellow]")


@favorites.command(name="remove")
@click.argument("court_name")
def remove_favorite(court_name: str):
    """
    Remove a court from favorites.

    Args:
        court_name: Name of the court to remove

    Examples:
        doral-courts favorites remove "DLP Tennis Court 1"
    """
    logger.info(f"Removing court from favorites: {court_name}")

    config = Config()

    if config.remove_favorite(court_name):
        console.print(f"[green]✅ Removed '{court_name}' from favorites[/green]")
    else:
        console.print(f"[red]'{court_name}' not found in favorites[/red]")
        console.print(
            "[blue]Use 'doral-courts favorites list' to see current favorites[/blue]"
        )
