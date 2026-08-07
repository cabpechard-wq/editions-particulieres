"""Cadre paragraphe pour callouts Notion — barre gauche alignée sur la marge du corps."""

from __future__ import annotations

from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Pt
from docx.text.paragraph import Paragraph

from .theme import (
    CALLOUT_BORDER_SHADE,
    CALLOUT_BORDER_SPACE,
    CALLOUT_BORDER_SZ,
    CALLOUT_BORDER_THEME,
    CALLOUT_PARA_SPACE_AFTER_PT,
)


def _clear_paragraph_shading(paragraph: Paragraph) -> None:
    pPr = paragraph._element.get_or_add_pPr()
    for old in pPr.findall(qn("w:shd")):
        pPr.remove(old)
    pPr.append(
        parse_xml(
            f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="FFFFFF"/>'
        )
    )
    for run in paragraph.runs:
        rPr = run._element.get_or_add_rPr()
        for old in rPr.findall(qn("w:shd")):
            rPr.remove(old)


def apply_callout_border(paragraph: Paragraph) -> None:
    """Barre bleue 3 pt à gauche, alignée sur le bord du corps de texte (comme Normal)."""
    _clear_paragraph_shading(paragraph)
    pPr = paragraph._element.get_or_add_pPr()
    for old in pPr.findall(qn("w:pBdr")):
        pPr.remove(old)
    pPr.append(
        parse_xml(
            f"<w:pBdr {nsdecls('w')}>"
            f'<w:left w:val="single" w:sz="{CALLOUT_BORDER_SZ}" '
            f'w:space="{CALLOUT_BORDER_SPACE}" w:color="auto" '
            f'w:themeColor="{CALLOUT_BORDER_THEME}" '
            f'w:themeShade="{CALLOUT_BORDER_SHADE}"/>'
            f"</w:pBdr>"
        )
    )
    pf = paragraph.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(CALLOUT_PARA_SPACE_AFTER_PT)


def finalize_callout_frames(paragraphs: list[Paragraph]) -> None:
    """Applique la barre gauche + interligne de corps sur chaque § du callout."""
    for paragraph in paragraphs:
        if not (paragraph.text or "").strip():
            continue
        apply_callout_border(paragraph)


def _box_border_xml() -> str:
    side = (
        f'w:val="single" w:sz="{CALLOUT_BORDER_SZ}" w:space="{CALLOUT_BORDER_SPACE}" '
        f'w:color="auto" w:themeColor="{CALLOUT_BORDER_THEME}" '
        f'w:themeShade="{CALLOUT_BORDER_SHADE}"'
    )
    return (
        f"<w:top {side}/><w:left {side}/><w:bottom {side}/><w:right {side}/>"
        f'<w:insideH w:val="nil"/><w:insideV w:val="nil"/>'
    )


def style_fiche_decision_table(table) -> None:
    """Cadre bleu 4 côtés + marges internes pour la fiche de décision."""
    from .theme import FICHE_BOX_CELL_MARGIN_DXA

    tbl = table._tbl
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = parse_xml(f"<w:tblPr {nsdecls('w')}/>")
        tbl.insert(0, tblPr)
    for old in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(old)
    tblPr.append(
        parse_xml(f"<w:tblBorders {nsdecls('w')}>{_box_border_xml()}</w:tblBorders>")
    )
    m = int(FICHE_BOX_CELL_MARGIN_DXA)
    for old in tblPr.findall(qn("w:tblCellMar")):
        tblPr.remove(old)
    tblPr.append(
        parse_xml(
            f"<w:tblCellMar {nsdecls('w')}>"
            f'<w:top w:w="{m}" w:type="dxa"/>'
            f'<w:left w:w="{m}" w:type="dxa"/>'
            f'<w:bottom w:w="{m}" w:type="dxa"/>'
            f'<w:right w:w="{m}" w:type="dxa"/>'
            f"</w:tblCellMar>"
        )
    )
    for old in tblPr.findall(qn("w:tblW")):
        tblPr.remove(old)
    tblPr.append(
        parse_xml(f'<w:tblW {nsdecls("w")} w:w="5000" w:type="pct"/>')
    )
