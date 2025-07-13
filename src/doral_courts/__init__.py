"""
Doral Courts CLI - Tennis and Pickleball Court Availability Tool.

A command-line interface for checking tennis and pickleball court availability
in Doral, Florida.
"""

__version__ = "0.1.0"
__author__ = "Jorge Barnaby"
__email__ = "jorge.barnaby@gmail.com"

from .core.html_extractor import Court, TimeSlot

__all__ = ["Court", "TimeSlot"]
