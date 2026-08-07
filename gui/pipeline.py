"""Exécution d'export GUI."""

from __future__ import annotations

from pathlib import Path

from .format_opts import ensure_format
from .request import PipelineRequest


def run_pipeline(req: PipelineRequest) -> tuple[int, list[Path]]:
    err = req.validate()
    if err:
        req.log(f"Erreur : {err}\n")
        return 1, []

    try:
        fmt = ensure_format(req.format or "docx")
    except ValueError as e:
        req.log(f"Erreur : {e}\n")
        return 1, []

    if fmt != "docx":
        from extract.html.export_pipeline import run_html_pipeline

        return run_html_pipeline(req)

    from extract.word.export_pipeline import run_word_pipeline

    return run_word_pipeline(req)
