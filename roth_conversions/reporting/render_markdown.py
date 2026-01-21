from __future__ import annotations

from .models import ReportDocument


def render_markdown(doc: ReportDocument) -> str:
    lines: list[str] = []
    lines.append(f"# {doc.title}")
    lines.append("")
    lines.append(f"Generated: {doc.short_created_at}")
    lines.append("")

    for section in doc.sections:
        lines.append(f"## {section.title}")
        lines.append("")

        for p in section.paragraphs:
            lines.append(p)
            lines.append("")

        for table in section.tables:
            headers = list(table.headers)
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
            for row in table.rows:
                lines.append("| " + " | ".join(str(x) for x in row) + " |")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"
