"""Demande d'export GUI (validation — exécution dans pipeline.py)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from packages.ep_core.registers import REGISTRE_ORDER

from .format_opts import ensure_format


@dataclass
class PipelineRequest:
    registres: list[str] = field(default_factory=list)
    autres: list[str] = field(default_factory=list)
    pages: list[str] = field(default_factory=list)
    pages_by_registre: dict[str, list[str]] = field(default_factory=dict)
    combine: bool = False
    name: str = ""
    limit: int | None = None
    out: Path = field(default_factory=Path)
    format: str = "docx"
    site_templates: Path | None = None
    arrets_refresh: bool = True
    arrets_a5: bool = False
    also_pdf: bool = False
    log: Callable[[str], None] = field(default=lambda _s: None)
    cancel: Callable[[], bool] = field(default=lambda: False)

    def validate(self) -> str | None:
        regs = [r for r in self.registres if r in REGISTRE_ORDER]
        if not regs and not any(a.strip() for a in self.autres):
            return "Sélectionnez au moins un registre ou une base « Autre(s) »."
        fmt = (self.format or "docx").lower().strip()
        if fmt == "html" and self.combine:
            return "HTML : l'export combiné n'est pas pris en charge."
        if self.arrets_a5 and (len(regs) != 1 or regs[0] != "arrets" or self.autres):
            return "Impression A5 : uniquement si Jurisprudence est la seule source."
        return None

    def queries_for(self, registre: str) -> list[str]:
        keyed = self.pages_by_registre.get(registre) or []
        if keyed:
            return list(keyed)
        return list(self.pages)
