"""Conversion .docx → .pdf via Microsoft Word (COM / pywin32)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import TracebackType
from typing import Any, Callable

_WD_FORMAT_PDF = 17


class WordPdfError(RuntimeError):
    """Word / pywin32 indisponible ou échec de conversion PDF."""


def _require_win32() -> None:
    if sys.platform != "win32":
        raise WordPdfError("L'export PDF nécessite Windows et Microsoft Word.")
    try:
        import pythoncom  # noqa: F401
        import win32com.client  # noqa: F401
    except ImportError as e:
        raise WordPdfError(
            "pywin32 est requis pour l'export PDF. "
            "pip install pywin32 — Microsoft Word doit aussi être installé."
        ) from e


def _configure_word(word: Any) -> None:
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        word.Options.SaveNormalPrompt = False
    except Exception:
        pass


def _safe_quit(word: Any) -> None:
    if word is None:
        return
    try:
        while int(word.Documents.Count) > 0:
            try:
                word.Documents(1).Close(SaveChanges=0)
            except Exception:
                break
    except Exception:
        pass
    try:
        word.NormalTemplate.Saved = True
    except Exception:
        pass
    try:
        word.Quit(SaveChanges=0)
    except Exception:
        pass


class WordApp:
    """Session Word courte durée pour conversions PDF en lot."""

    def __init__(self) -> None:
        self._word: Any = None
        self._owned = False

    def __enter__(self) -> WordApp:
        _require_win32()
        import pythoncom
        import win32com.client

        pythoncom.CoInitialize()
        self._owned = True
        try:
            self._word = win32com.client.DispatchEx("Word.Application")
            _configure_word(self._word)
        except Exception as e:
            pythoncom.CoUninitialize()
            self._owned = False
            raise WordPdfError(f"Impossible de démarrer Word : {e}") from e
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        import gc

        _safe_quit(self._word)
        self._word = None
        gc.collect()
        if self._owned:
            import pythoncom

            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
            self._owned = False

    @property
    def app(self) -> Any:
        if self._word is None:
            raise WordPdfError("WordApp non ouverte.")
        return self._word


def _convert_with_app(word: Any, docx_path: Path, pdf_path: Path) -> Path:
    doc = None
    try:
        doc = word.Documents.Open(
            str(docx_path.resolve()),
            ReadOnly=True,
            AddToRecentFiles=False,
        )
        try:
            doc.Fields.Update()
        except Exception:
            pass
        try:
            for i in range(1, int(doc.TablesOfContents.Count) + 1):
                doc.TablesOfContents(i).Update()
        except Exception:
            pass
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        doc.SaveAs(str(pdf_path.resolve()), FileFormat=_WD_FORMAT_PDF)
    except Exception as e:
        raise WordPdfError(f"Conversion PDF échouée ({docx_path.name}) : {e}") from e
    finally:
        if doc is not None:
            try:
                doc.Close(False)
            except Exception:
                pass
    return pdf_path


def docx_to_pdf(
    docx_path: Path,
    pdf_path: Path | None = None,
    *,
    app: Any | None = None,
) -> Path:
    docx_path = Path(docx_path)
    if not docx_path.is_file():
        raise FileNotFoundError(docx_path)
    pdf_path = Path(pdf_path) if pdf_path else docx_path.with_suffix(".pdf")

    if app is not None:
        return _convert_with_app(app, docx_path, pdf_path)

    with WordApp() as session:
        return _convert_with_app(session.app, docx_path, pdf_path)


def convert_docx_list_to_pdf(
    docx_paths: list[Path],
    *,
    log: Callable[[str], None] | None = None,
    cancel: Callable[[], bool] | None = None,
) -> tuple[list[Path], int]:
    """Post-traitement : convertit des .docx déjà générés en .pdf (même dossier)."""
    _log = log or (lambda _s: None)
    paths = [Path(p) for p in docx_paths if Path(p).suffix.lower() == ".docx"]
    if not paths:
        return [], 0

    produced: list[Path] = []
    errors = 0
    try:
        with WordApp() as session:
            for docx in paths:
                if cancel and cancel():
                    _log("Annulé — conversion PDF.\n")
                    break
                pdf = docx.with_suffix(".pdf")
                _log(f"  PDF : {docx.name} -> {pdf.name}\n")
                try:
                    docx_to_pdf(docx, pdf, app=session.app)
                    produced.append(pdf)
                except (WordPdfError, OSError) as e:
                    errors += 1
                    _log(f"  x {docx.name} : {e}\n")
    except WordPdfError as e:
        _log(f"Erreur PDF : {e}\n")
        return [], 1

    return produced, errors


def convert_tree(
    root: Path,
    *,
    log: Callable[[str], None] | None = None,
    cancel: Callable[[], bool] | None = None,
) -> tuple[list[Path], int]:
    """Convertit tous les .docx sous root en .pdf."""
    docx_files = [
        p
        for p in sorted(Path(root).rglob("*.docx"))
        if not p.name.startswith("~$")
    ]
    return convert_docx_list_to_pdf(docx_files, log=log, cancel=cancel)
