"""Main CLI entry point for Doral Courts application."""

import click

from ..utils.logger import setup_logging
from .commands.analyze_cmd import analyze
from .commands.cleanup_cmd import cleanup
from .commands.data_cmd import data
from .commands.favorites_cmd import favorites
from .commands.history_cmd import history
from .commands.list_available_slots_cmd import list_available_slots
from .commands.list_cmd import list_courts
from .commands.list_courts_cmd import list_courts as list_courts_names
from .commands.list_locations_cmd import list_locations
from .commands.monitor_cmd import monitor
from .commands.query_cmd import query
from .commands.slots_cmd import slots
from .commands.stats_cmd import stats
from .commands.watch_cmd import watch


@click.group()
@click.version_option(version="0.1.0")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option(
    "--save-data", is_flag=True, help="Save retrieved HTML and JSON data to files"
)
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
        doral-courts --save-data list --date tomorrow
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["save_data"] = save_data
    setup_logging(verbose=verbose)


# Add commands to the CLI group
cli.add_command(list_courts, name="list")
cli.add_command(stats)
cli.add_command(slots)
cli.add_command(data)
cli.add_command(cleanup)
cli.add_command(history)
cli.add_command(watch)
cli.add_command(monitor)
cli.add_command(analyze)
cli.add_command(list_available_slots)
cli.add_command(list_courts_names)
cli.add_command(list_locations)
cli.add_command(favorites)
cli.add_command(query)


if __name__ == "__main__":
    cli()
