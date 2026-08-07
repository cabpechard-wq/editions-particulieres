"""Rich text Notion → runs Word."""

from __future__ import annotations

from typing import Any
from xml.sax.saxutils import escape

from docx.oxml import parse_xml
from docx.shared import RGBColor
from docx.text.paragraph import Paragraph

from packages.ep_core.notion.ids import page_url_from_id, to_uuid

NOTION_TEXT_COLORS: dict[str, str] = {
    "gray": "787774",
    "brown": "976D57",
    "orange": "D9730D",
    "yellow": "CB912F",
    "green": "448361",
    "blue": "337EA9",
    "purple": "9065B0",
    "pink": "C14C8A",
    "red": "E03E3E",
}


def rich_plain(rich_texts: list[dict[str, Any]] | None) -> str:
    return "".join(rt.get("plain_text", "") for rt in (rich_texts or [])).strip()


def split_notion_color(raw: str | None) -> tuple[str | None, bool]:
    color = (raw or "default").strip().lower()
    if color in {"", "default"}:
        return None, False
    if color.endswith("_background"):
        return None, True
    if color in NOTION_TEXT_COLORS:
        return color, False
    base = color.split("_")[0]
    if base in NOTION_TEXT_COLORS:
        return base, False
    return None, False


def notion_color_hex(name: str | None) -> str | None:
    if not name:
        return None
    return NOTION_TEXT_COLORS.get(name)


def annotation_to_run_kwargs(annotations: dict[str, Any] | None) -> dict[str, Any]:
    ann = annotations or {}
    color_name, is_bg = split_notion_color(ann.get("color"))
    color_hex = None if is_bg else notion_color_hex(color_name)
    return {
        "color_hex": color_hex,
        "bold": bool(ann.get("bold")),
        "italic": bool(ann.get("italic")),
        "underline": bool(ann.get("underline")),
        "strikethrough": bool(ann.get("strikethrough")),
        "code": bool(ann.get("code")),
    }


def _apply_run_style(run, kwargs: dict[str, Any]) -> None:
    run.bold = bool(kwargs.get("bold"))
    run.italic = bool(kwargs.get("italic"))
    run.underline = bool(kwargs.get("underline"))
    if kwargs.get("strikethrough"):
        run.font.strike = True
    if kwargs.get("code"):
        run.font.name = "Consolas"
    hex_color = kwargs.get("color_hex")
    if hex_color:
        run.font.color.rgb = RGBColor.from_string(hex_color.upper())


def _hyperlink_url(rt: dict[str, Any]) -> str | None:
    href = rt.get("href")
    if rt.get("type") == "mention":
        mention = rt.get("mention") or {}
        mtype = mention.get("type")
        if mtype == "page":
            pid = (mention.get("page") or {}).get("id")
            if pid:
                return page_url_from_id(pid)
        if mtype == "link_preview":
            return (mention.get("link_preview") or {}).get("url") or href
    if href:
        return href
    link = (rt.get("text") or {}).get("link")
    if link:
        return link.get("url")
    return None


def add_hyperlink(
    paragraph: Paragraph,
    text: str,
    url: str,
    *,
    color_hex: str | None = None,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
) -> None:
    if not url:
        run = paragraph.add_run(text)
        _apply_run_style(run, {"color_hex": color_hex, "bold": bold, "italic": italic, "underline": underline})
        return

    part = paragraph.part
    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    rpr_bits: list[str] = []
    if color_hex:
        h = color_hex.strip().lstrip("#").upper()
        if len(h) == 6:
            rpr_bits.append(f'<w:color w:val="{h}"/>')
    else:
        rpr_bits.append('<w:rStyle w:val="Hyperlink"/>')
    if bold:
        rpr_bits.append("<w:b/>")
    if italic:
        rpr_bits.append("<w:i/>")
    if underline:
        rpr_bits.append("<w:u w:val=\"single\"/>")
    rpr = "".join(rpr_bits)

    hyperlink = parse_xml(
        f'<w:hyperlink r:id="{r_id}" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        f'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>'
    )
    run = parse_xml(
        f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:rPr>{rpr}</w:rPr>"
        f'<w:t xml:space="preserve">{escape(text)}</w:t>'
        f"</w:r>"
    )
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def append_rich_text(
    paragraph: Paragraph,
    rich_texts: list[dict[str, Any]],
    *,
    resolve_title: Any | None = None,
) -> None:
    for rt in rich_texts or []:
        text = rt.get("plain_text") or ""
        if not text:
            continue
        kwargs = annotation_to_run_kwargs(rt.get("annotations") or {})
        url = _hyperlink_url(rt)
        if url and resolve_title and rt.get("type") == "mention":
            try:
                pid = to_uuid(url)
                resolved = (resolve_title(pid) or "").strip()
                if resolved:
                    text = resolved
            except ValueError:
                pass
        if url:
            add_hyperlink(
                paragraph,
                text,
                url,
                color_hex=kwargs.get("color_hex"),
                bold=kwargs.get("bold", False),
                italic=kwargs.get("italic", False),
                underline=kwargs.get("underline", False),
            )
            continue
        run = paragraph.add_run(text)
        _apply_run_style(run, kwargs)
