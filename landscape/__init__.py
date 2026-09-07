"""target-landscape — competitive landscape memos for drug targets from public data."""

from .pipeline import build, load_fixture, save_fixture
from .render import to_html, to_markdown

__version__ = "0.1.0"
__all__ = ["build", "load_fixture", "save_fixture", "to_html", "to_markdown"]
