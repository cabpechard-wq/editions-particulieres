"""Modèle Word unique + attache native (linkStyles) pour mise à jour des styles."""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

from .styles import STYLE_H1, template_path

R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
ATTACHED_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/attachedTemplate"
)

SETTINGS = "word/settings.xml"
SETTINGS_RELS = "word/_rels/settings.xml.rels"


def _dotx_has_style(path: Path, style_name: str) -> bool:
    if not path.exists():
        return False
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/styles.xml").decode("utf-8", errors="ignore")
    except (OSError, zipfile.BadZipFile, KeyError):
        return False
    return f'w:val="{style_name}"' in xml


def master_styles_path() -> Path:
    """Retourne Editions_Particulieres.dotx s'il contient les styles attendus."""
    primary = template_path()
    if _dotx_has_style(primary, STYLE_H1):
        return primary
    return primary


def _xml_escape_attr(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _default_settings_xml() -> bytes:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:settings xmlns:r="{R_NS}" xmlns:w="{W_NS}">'
        "</w:settings>"
    ).encode("utf-8")


def _build_settings_rels(template_uri: str, rel_id: str) -> bytes:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{PKG_REL_NS}">'
        f'<Relationship Id="{rel_id}" Type="{ATTACHED_REL_TYPE}" '
        f'Target="{_xml_escape_attr(template_uri)}" TargetMode="External"/>'
        "</Relationships>"
    ).encode("utf-8")


def _patch_settings_xml(settings_xml: bytes, *, rel_id: str, link_styles: bool) -> bytes:
    text = settings_xml.decode("utf-8")

    if "xmlns:r=" not in text:
        text = re.sub(
            r"<w:settings\b",
            f'<w:settings xmlns:r="{R_NS}"',
            text,
            count=1,
        )

    text = re.sub(r"<w:attachedTemplate\b[^/]*/>", "", text)
    text = re.sub(
        r"<w:attachedTemplate\b[^>]*>.*?</w:attachedTemplate>",
        "",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(r"<w:linkStyles\b[^/]*/>", "", text)
    text = re.sub(
        r"<w:linkStyles\b[^>]*>.*?</w:linkStyles>",
        "",
        text,
        flags=re.DOTALL,
    )

    insert = f'<w:attachedTemplate r:id="{rel_id}"/>'
    if link_styles:
        insert += "<w:linkStyles/>"

    text = re.sub(r"(<w:settings\b[^>]*>)", r"\1" + insert, text, count=1)
    return text.encode("utf-8")


def attach_template(
    docx_path: Path,
    template_path_arg: Path,
    *,
    link_styles: bool = True,
) -> None:
    """Attache un .dotx au .docx et active « Mettre à jour automatiquement les styles »."""
    docx_path = Path(docx_path)
    template_path_arg = Path(template_path_arg).resolve()
    if not docx_path.exists():
        raise FileNotFoundError(docx_path)
    if not template_path_arg.exists():
        raise FileNotFoundError(f"Modèle de styles introuvable : {template_path_arg}")

    template_uri = template_path_arg.as_uri()
    rel_id = "rIdAttachedTemplate"

    buf = io.BytesIO()
    with zipfile.ZipFile(docx_path, "r") as zin, zipfile.ZipFile(
        buf, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        names = set(zin.namelist())
        settings = zin.read(SETTINGS) if SETTINGS in names else _default_settings_xml()
        settings = _patch_settings_xml(settings, rel_id=rel_id, link_styles=link_styles)
        rels = _build_settings_rels(template_uri, rel_id=rel_id)

        for item in zin.infolist():
            if item.filename in {SETTINGS, SETTINGS_RELS}:
                continue
            zout.writestr(item, zin.read(item.filename))
        zout.writestr(SETTINGS, settings)
        zout.writestr(SETTINGS_RELS, rels)

    docx_path.write_bytes(buf.getvalue())


def attach_master_styles(docx_path: Path, *, master: Path | None = None) -> None:
    attach_template(docx_path, master or master_styles_path(), link_styles=True)


def relink_tree(
    root: Path,
    *,
    master: Path | None = None,
    pattern: str = "*.docx",
) -> list[Path]:
    """Ré-attache le master sur tous les .docx sous root."""
    master = Path(master or master_styles_path())
    done: list[Path] = []
    for path in sorted(Path(root).rglob(pattern)):
        if path.name.startswith("~$"):
            continue
        attach_master_styles(path, master=master)
        done.append(path)
    return done
