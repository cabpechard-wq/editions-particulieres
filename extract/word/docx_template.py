"""Ouverture de modèles .dotx/.docx."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from docx import Document

CT_DOC = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
CT_TPL = "application/vnd.openxmlformats-officedocument.wordprocessingml.template.main+xml"


def dotx_to_docx_bytes(template_path: Path) -> bytes:
    template_path = Path(template_path)
    if not template_path.exists():
        raise FileNotFoundError(f"Modèle introuvable : {template_path}")
    buf = io.BytesIO()
    with zipfile.ZipFile(template_path, "r") as zin, zipfile.ZipFile(
        buf, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml":
                data = data.decode("utf-8").replace(CT_TPL, CT_DOC).encode("utf-8")
            zout.writestr(item, data)
    return buf.getvalue()


def clear_document_body(doc: Document) -> None:
    body = doc.element.body
    for child in list(body):
        if child.tag.endswith("sectPr"):
            continue
        body.remove(child)


def open_from_template(template_path: Path, *, clear_body: bool = True) -> Document:
    data = dotx_to_docx_bytes(Path(template_path))
    doc = Document(io.BytesIO(data))
    if clear_body:
        clear_document_body(doc)
    return doc
