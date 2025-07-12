import json
from pathlib import Path
from datetime import datetime
from typing import List
from rich.console import Console
from rich.table import Table
from html_extractor import Court
from logger import get_logger

logger = get_logger(__name__)
console = Console()

def save_html_data(html_content: str, filename_suffix: str = "") -> str:
    """Save HTML content to a file in the data directory."""
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"doral_courts_{timestamp}{filename_suffix}.html"
    filepath = data_dir / filename
    
    # Save HTML content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Saved HTML data to {filepath}")
    return str(filepath)

def save_json_data(courts: List[Court], filename_suffix: str = "") -> str:
    """Save court data as JSON to a file in the data directory."""
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"doral_courts_{timestamp}{filename_suffix}.json"
    filepath = data_dir / filename
    
    # Convert courts to JSON-serializable format
    courts_data = []
    for court in courts:
        court_dict = {
            "name": court.name,
            "sport_type": court.sport_type,
            "location": court.location,
            "surface_type": court.surface_type,
            "availability_status": court.availability_status,
            "date": court.date,
            "price": court.price,
            "time_slots": [
                {
                    "start_time": slot.start_time,
                    "end_time": slot.end_time,
                    "status": slot.status
                }
                for slot in court.time_slots
            ]
        }
        courts_data.append(court_dict)
    
    # Create the full data structure
    json_data = {
        "timestamp": datetime.now().isoformat(),
        "total_courts": len(courts),
        "courts": courts_data
    }
    
    # Save JSON content
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved JSON data to {filepath}")
    return str(filepath)

def display_courts_table(courts: List[Court]):
    """Display courts in a formatted table."""
    table = Table(title="Doral Courts Availability")

    table.add_column("Court Name", style="cyan", no_wrap=True)
    table.add_column("Sport", style="magenta")
    table.add_column("Date", style="green")
    table.add_column("Time Slots", style="yellow")
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

        # Format time slots display
        if court.time_slots:
            available_count = sum(1 for slot in court.time_slots if slot.status == "Available")
            total_count = len(court.time_slots)
            time_display = f"{available_count}/{total_count} available"
        else:
            time_display = "No slots"

        table.add_row(
            court.name,
            court.sport_type,
            court.date,
            time_display,
            f"{status_style}{court.availability_status}[/]",
            court.surface_type,
            court.price or "N/A"
        )

    console.print(table)