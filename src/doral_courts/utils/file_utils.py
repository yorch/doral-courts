"""File operations and data persistence utilities."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..core.html_extractor import Court
from .logger import get_logger

logger = get_logger(__name__)


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
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"Saved HTML data to {filepath}")
    return str(filepath)


def save_json_data(
    courts: List[Court], filename_suffix: str = "", source_url: Optional[str] = None
) -> str:
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
            "capacity": court.capacity,
            "availability_status": court.availability_status,
            "date": court.date,
            "price": court.price,
            "time_slots": [
                {
                    "start_time": slot.start_time,
                    "end_time": slot.end_time,
                    "status": slot.status,
                }
                for slot in court.time_slots
            ],
        }
        courts_data.append(court_dict)

    # Create the full data structure
    json_data = {
        "timestamp": datetime.now().isoformat(),
        "total_courts": len(courts),
        "source_url": source_url,
        "courts": courts_data,
    }

    # Save JSON content
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved JSON data to {filepath}")
    return str(filepath)
