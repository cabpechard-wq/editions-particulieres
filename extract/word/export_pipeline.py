"""Pipeline d'export Word — branché sur la GUI."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from docx import Document
from docx.enum.text import WD_BREAK

from packages.ep_core.naming import stamped_path
from packages.ep_core.notion import NotionFetcher, page_title
from packages.ep_core.paths import resolve_path
from packages.ep_core.registers import REGISTRE_ORDER, database_url_for_registre

from extract.pull._common import load_env, make_fetcher, notion_token
from extract.word.converter import PageConverter
from extract.word.docx_template import open_from_template
from extract.word.index_docx import IndexConverter
from extract.word.jurisprudence_docx import JurisprudenceConverter
from extract.word.pages import filename_for_page, load_notion_pages, sort_pages_by_reference
from extract.word.styles_master import attach_master_styles, master_styles_path

RegistreKind = Literal["manuel", "fiches", "methodo", "formule", "index", "arrets", "autre"]


@dataclass
class _Unit:
    kind: RegistreKind
    label: str
    page: dict[str, Any] | None = None
    blocks: list[dict[str, Any]] | None = None
    page_id: str | None = None


def _unit_out_dir(out_dir: Path, kind: str, *, a5: bool = False) -> Path:
    name = "arrets_a5" if (kind == "arrets" and a5) else (
        "manuel" if kind == "autre" else kind
    )
    if out_dir.name in {
        "manuel",
        "fiches",
        "methodo",
        "formule",
        "index",
        "arrets",
        "arrets_a5",
    }:
        return out_dir
    return out_dir / name


def _default_combine_name(regs: list[str], autres: list[str]) -> str:
    bits = [r for r in REGISTRE_ORDER if r in regs]
    if any(a.strip() for a in autres):
        bits.append("autre")
    return "-".join(bits) if bits else "Export"


def _load_jurisprudence_pages(req, fetcher: NotionFetcher | None) -> list[dict[str, Any]]:
    json_path = resolve_path("matrices_jurisprudence") / "jurisprudence.json"
    if req.arrets_refresh or not json_path.is_file():
        from extract.pull.jurisprudence import export_jurisprudence

        req.log("Jurisprudence — mise à jour depuis Notion…\n")
        export_jurisprudence(output=json_path, limit=req.limit)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    pages = data.get("pages") or []
    queries = req.queries_for("arrets")
    if queries:
        qset = {q.strip().casefold() for q in queries}
        filtered = []
        for page in pages:
            pid = (page.get("id") or "").casefold()
            title = (page.get("title") or "").casefold()
            if any(q in pid or q in title for q in qset):
                filtered.append(page)
        pages = filtered
    if req.limit:
        pages = pages[: req.limit]
    return pages


def _collect_units(req) -> tuple[list[_Unit], int]:
    """Retourne (units, code). code != 0 si erreur fatale."""
    units: list[_Unit] = []
    fetcher: NotionFetcher | None = None
    consumed: set[str] = set()

    def cancelled() -> bool:
        try:
            return bool(req.cancel())
        except Exception:
            return False

    try:
        token = notion_token()
    except ValueError:
        token = ""

    for reg in REGISTRE_ORDER:
        if reg not in req.registres:
            continue
        if cancelled():
            req.log("Annulé.\n")
            return [], 130

        if reg == "arrets":
            try:
                if req.arrets_refresh or token:
                    if fetcher is None and token:
                        fetcher = make_fetcher()
                rows = _load_jurisprudence_pages(req, fetcher)
            except Exception as e:
                req.log(f"Erreur jurisprudence : {e}\n")
                return [], 1
            for row in rows:
                page = JurisprudenceConverter.from_json_page(row)
                units.append(
                    _Unit(
                        kind="arrets",
                        label=row.get("title") or "arrêt",
                        page=page,
                        blocks=[],
                        page_id=row.get("id"),
                    )
                )
            continue

        if not token:
            req.log("Erreur : NOTION_TOKEN manquant (.env).\n")
            return [], 1
        if fetcher is None:
            fetcher = make_fetcher()

        try:
            db = database_url_for_registre(reg)
        except ValueError as e:
            req.log(f"Erreur : {e}\n")
            return [], 1

        pages = load_notion_pages(
            fetcher,
            database=db,
            page_queries=req.queries_for(reg),
            limit=req.limit,
            log=req.log,
            exclude_ids=consumed,
        )
        pages = sort_pages_by_reference(pages)
        for page in pages:
            if cancelled():
                req.log("Annulé.\n")
                return [], 130
            consumed.add(page["id"])
            try:
                blocks = fetcher.get_block_tree(page["id"])
            except Exception as e:
                req.log(f"  x {page_title(page)} : {e}\n")
                continue
            units.append(
                _Unit(
                    kind=reg,  # type: ignore[arg-type]
                    label=page_title(page) or page["id"][:8],
                    page=page,
                    blocks=blocks,
                    page_id=page["id"],
                )
            )

    for autre_db in req.autres:
        db = autre_db.strip()
        if not db:
            continue
        if cancelled():
            req.log("Annulé.\n")
            return [], 130
        if not token:
            req.log("Erreur : NOTION_TOKEN manquant (.env).\n")
            return [], 1
        if fetcher is None:
            fetcher = make_fetcher()
        req.log(f"Autre base : {db}\n")
        pages = load_notion_pages(
            fetcher,
            database=db,
            page_queries=req.pages,
            limit=req.limit,
            log=req.log,
            exclude_ids=consumed,
        )
        pages = sort_pages_by_reference(pages)
        for page in pages:
            if cancelled():
                req.log("Annulé.\n")
                return [], 130
            consumed.add(page["id"])
            try:
                blocks = fetcher.get_block_tree(page["id"])
            except Exception as e:
                req.log(f"  x {page_title(page)} : {e}\n")
                continue
            units.append(
                _Unit(
                    kind="autre",
                    label=page_title(page) or page["id"][:8],
                    page=page,
                    blocks=blocks,
                    page_id=page["id"],
                )
            )

    if not units:
        req.log("Aucune fiche à exporter.\n")
        return [], 1
    return units, 0


def _converter_for(
    kind: str,
    template: Path,
    fetcher: NotionFetcher | None,
) -> PageConverter:
    if kind == "index":
        return IndexConverter(template, fetcher)
    if kind == "arrets":
        return JurisprudenceConverter(template, fetcher)
    return PageConverter(template, fetcher)


def _render_unit(
    doc: Document,
    unit: _Unit,
    template: Path,
    fetcher: NotionFetcher | None,
) -> None:
    conv = _converter_for(unit.kind, template, fetcher)
    assert unit.page is not None
    conv.render_into(doc, unit.page, unit.blocks or [])


def _save_doc(doc: Document, path: Path, template: Path) -> Path:
    from .typo_polish import polish_document

    polish_document(doc)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(path))
    if template.exists():
        attach_master_styles(path, master=template)
    return path


def run_word_pipeline(req) -> tuple[int, list[Path]]:
    load_env()
    units, code = _collect_units(req)
    if code != 0:
        return code, []

    out_dir = Path(req.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    template = master_styles_path()
    if not template.exists():
        req.log(f"Erreur : modèle introuvable : {template}\n")
        return 1, []

    only_arrets = req.registres == ["arrets"] and not any(a.strip() for a in req.autres)
    a5 = bool(only_arrets and req.arrets_a5)

    fetcher: NotionFetcher | None = None
    try:
        fetcher = make_fetcher()
    except Exception:
        fetcher = None

    req.log(f"{len(units)} fiche(s) -> {out_dir}\n\n")
    produced: list[Path] = []
    errors = 0

    if req.combine:
        stem = (req.name or "").strip() or _default_combine_name(req.registres, req.autres)
        combine_dir = _unit_out_dir(out_dir, "arrets", a5=a5) if a5 else out_dir
        out_path = stamped_path(combine_dir, stem, ext=".docx")
        req.log(f"Combiner -> {out_path.name}\n")
        doc = open_from_template(template)
        ok = 0
        for i, unit in enumerate(units):
            if req.cancel():
                req.log("Annulé.\n")
                return (1 if not produced else 130), produced
            if ok > 0:
                p = doc.add_paragraph()
                p.add_run().add_break(WD_BREAK.PAGE)
            req.log(f"  [{i + 1}/{len(units)}] {unit.kind} - {unit.label}\n")
            try:
                _render_unit(doc, unit, template, fetcher)
                ok += 1
            except Exception as e:
                errors += 1
                req.log(f"  x {unit.label} : {e}\n")
        if ok == 0:
            req.log("Aucune fiche rendue.\n")
            return 1, []
        _save_doc(doc, out_path, template)
        produced.append(out_path)
        req.log(f"OK {out_path} ({ok} fiche(s), {errors} erreur(s))\n")
        if req.also_pdf:
            pdfs, pdf_errors = _postprocess_pdf(produced, req)
            produced.extend(pdfs)
            errors += pdf_errors
        return (1 if errors else 0), produced

    for i, unit in enumerate(units):
        if req.cancel():
            req.log("Annulé.\n")
            return (1 if errors else 130), produced
        unit_dir = _unit_out_dir(out_dir, unit.kind, a5=a5 and unit.kind == "arrets")
        if unit.page:
            base = filename_for_page(unit.page, unit.label)
        else:
            from packages.ep_core.naming import sanitize_filename

            base = sanitize_filename(unit.label)
        out_path = stamped_path(unit_dir, base, ext=".docx")
        req.log(f"[{i + 1}/{len(units)}] {unit.kind} - {unit.label} -> {out_path.name}\n")
        try:
            doc = open_from_template(template)
            _render_unit(doc, unit, template, fetcher)
            _save_doc(doc, out_path, template)
            produced.append(out_path)
        except Exception as e:
            errors += 1
            req.log(f"  x {e}\n")

    if req.also_pdf and produced:
        req.log("\nPost-traitement PDF…\n")
        pdfs, pdf_errors = _postprocess_pdf(produced, req)
        produced.extend(pdfs)
        errors += pdf_errors

    req.log(f"Terminé : {len(produced)} fichier(s), {errors} erreur(s)\n")
    return (1 if errors else 0), produced


def _postprocess_pdf(produced: list[Path], req) -> tuple[list[Path], int]:
    from .word_pdf import convert_docx_list_to_pdf

    docx_only = [p for p in produced if p.suffix.lower() == ".docx"]
    pdfs, pdf_errors = convert_docx_list_to_pdf(
        docx_only,
        log=req.log,
        cancel=req.cancel,
    )
    if pdfs:
        req.log(f"{len(pdfs)} PDF créé(s).\n")
    return pdfs, pdf_errors
