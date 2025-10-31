"""Saved queries command implementation."""

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ...core.database import Database
from ...core.scraper import Scraper
from ...display.tables import display_courts_table
from ...utils.config import Config
from ...utils.date_utils import parse_date_input
from ...utils.file_utils import save_html_data, save_json_data
from ...utils.logger import get_logger

logger = get_logger(__name__)
console = Console()


@click.command(name="query")
@click.argument("query_name")
@click.pass_context
def query(ctx, query_name: str):
    """
    Run a saved query by name.

    Executes a pre-configured query with saved parameters (sport, date, status, etc.).
    Queries are stored in ~/.doral-courts/config.yaml and can be created manually.

    Args:
        query_name: Name of the saved query to execute

    Examples:
        doral-courts query my_tennis
        doral-courts query weekend_pickleball

    Query Configuration (in config.yaml):
        queries:
          my_tennis:
            sport: tennis
            date: tomorrow
            status: available
          weekend_pickleball:
            sport: pickleball
            date: "+2"
            location: "Doral Central Park"
    """
    logger.info(f"Executing saved query: {query_name}")

    config = Config()
    query_params = config.get_query(query_name)

    if not query_params:
        console.print(f"[red]Query '{query_name}' not found[/red]")
        console.print(
            "[blue]Available queries:[/blue]"
        )

        # Show available queries
        all_queries = config.get_queries()
        if all_queries:
            table = Table(show_header=True)
            table.add_column("Query Name", style="cyan")
            table.add_column("Parameters", style="dim")

            for name, params in all_queries.items():
                params_str = ", ".join(f"{k}={v}" for k, v in params.items())
                table.add_row(name, params_str)

            console.print(table)
        else:
            console.print("[yellow]No saved queries configured[/yellow]")
            console.print(
                "[dim]Edit ~/.doral-courts/config.yaml to add queries[/dim]"
            )

        return

    # Show query info
    console.print(f"[blue]Running query:[/blue] [cyan]{query_name}[/cyan]")
    params_str = ", ".join(f"{k}={v}" for k, v in query_params.items())
    console.print(f"[dim]Parameters: {params_str}[/dim]\n")

    # Extract parameters
    sport = query_params.get("sport")
    date = query_params.get("date")
    status = query_params.get("status")
    location = query_params.get("location")

    # Parse date if provided
    try:
        parsed_date = parse_date_input(date) if date else parse_date_input(None)
    except ValueError as e:
        console.print(f"[red]Error in query date parameter: {e}[/red]")
        return

    logger.debug(
        f"Query parameters - Sport: {sport}, Date: {date} -> {parsed_date}, "
        f"Status: {status}, Location: {location}"
    )

    db = Database()

    # Fetch fresh data from website
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
            courts, html_content = scraper.fetch_courts_with_html(
                date=parsed_date, sport_filter=sport
            )
        else:
            courts = scraper.fetch_courts(date=parsed_date, sport_filter=sport)
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
                    html_path = save_html_data(html_content, f"_query_{query_name}")
                    json_path = save_json_data(
                        courts, f"_query_{query_name}", scraper.get_last_request_url()
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

    # Apply filters to fresh data
    logger.debug("Applying query filters to fresh data")
    filtered_courts = courts

    if sport:
        filtered_courts = [
            court
            for court in filtered_courts
            if court.sport_type.lower() == sport.lower()
        ]
        logger.debug(
            f"Applied sport filter '{sport}': {len(courts)} -> {len(filtered_courts)} courts"
        )

    if status:
        filtered_courts = [
            court
            for court in filtered_courts
            if status.lower() in court.availability_status.lower()
        ]
        logger.debug(f"Applied status filter '{status}': {len(filtered_courts)} courts")

    if location:
        filtered_courts = [
            court
            for court in filtered_courts
            if location.lower() in court.location.lower()
        ]
        logger.debug(
            f"Applied location filter '{location}': {len(filtered_courts)} courts"
        )

    logger.info(f"Found {len(filtered_courts)} courts matching query criteria")

    if not filtered_courts:
        console.print("[red]No courts found matching your query criteria.[/red]")
        return

    # Display courts in a table
    logger.debug("Displaying courts table")
    display_courts_table(filtered_courts)
