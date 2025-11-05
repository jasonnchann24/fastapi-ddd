"""Logging utilities for FastAPI DDD."""

from rich.console import Console
from rich.text import Text

console = Console()


def log_info(msg: str):
    """Log an info message with FastAPI 3D branding."""
    label = Text(" FastAPI 3D✨ ", style="bold bright_white on deep_sky_blue1")
    console.print(label, msg)
