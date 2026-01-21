from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Sequence


@dataclass(frozen=True)
class ReportTable:
    headers: Sequence[str]
    rows: Sequence[Sequence[str]]


@dataclass(frozen=True)
class ReportSection:
    title: str
    paragraphs: Sequence[str] = field(default_factory=tuple)
    tables: Sequence[ReportTable] = field(default_factory=tuple)


@dataclass(frozen=True)
class ReportDocument:
    title: str
    created_at: datetime
    sections: Sequence[ReportSection]

    @property
    def short_created_at(self) -> str:
        return self.created_at.strftime("%Y-%m-%d %H:%M")
