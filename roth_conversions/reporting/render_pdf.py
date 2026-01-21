from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from .models import ReportDocument


def render_pdf(doc: ReportDocument, *, out_path: str | Path) -> Path:
    """Render to a simple, email-friendly PDF.

    Implementation uses ReportLab (pure Python). If it's not installed,
    raise a helpful error.
    """

    try:
        colors = importlib.import_module("reportlab.lib.colors")
        pagesizes = importlib.import_module("reportlab.lib.pagesizes")
        styles_mod = importlib.import_module("reportlab.lib.styles")
        platypus = importlib.import_module("reportlab.platypus")
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "PDF rendering requires the 'reportlab' package. "
            "Install it with: uv add reportlab (then uv sync), or pip install reportlab"
        ) from e

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    letter = getattr(pagesizes, "letter")
    getSampleStyleSheet = getattr(styles_mod, "getSampleStyleSheet")
    Paragraph = getattr(platypus, "Paragraph")
    SimpleDocTemplate = getattr(platypus, "SimpleDocTemplate")
    Spacer = getattr(platypus, "Spacer")
    Table = getattr(platypus, "Table")
    TableStyle = getattr(platypus, "TableStyle")

    styles = getSampleStyleSheet()
    story: list[Any] = []

    story.append(Paragraph(doc.title, styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Generated: {doc.short_created_at}", styles["Normal"]))
    story.append(Spacer(1, 18))

    for section in doc.sections:
        story.append(Paragraph(section.title, styles["Heading2"]))
        story.append(Spacer(1, 8))

        for p in section.paragraphs:
            story.append(Paragraph(p, styles["Normal"]))
            story.append(Spacer(1, 6))

        for t in section.tables:
            data = [list(t.headers)] + [list(r) for r in t.rows]
            tbl = Table(data, hAlign="LEFT")
            tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#efefef")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                        ("TOPPADDING", (0, 0), (-1, 0), 6),
                    ]
                )
            )
            story.append(tbl)
            story.append(Spacer(1, 14))

        story.append(Spacer(1, 10))

    SimpleDocTemplate(str(out_path), pagesize=letter, title=doc.title).build(story)
    return out_path
