"""Reporting layer.

Builds structured report sections from analysis outputs, then renders to Markdown or PDF.
"""

from .models import ReportDocument, ReportSection, ReportTable
from .builder import build_report
from .render_markdown import render_markdown

__all__ = [
    "ReportDocument",
    "ReportSection",
    "ReportTable",
    "build_report",
    "render_markdown",
]
