"""Rich text Notion → HTML."""

from __future__ import annotations

import html
from typing import Any, Callable

from packages.ep_core.notion.ids import page_url_from_id, to_uuid

NOTION_TEXT_COLORS: dict[str, str] = {
    "gray": "#787774",
    "brown": "#976D57",
    "orange": "#D9730D",
    "yellow": "#CB912F",
    "green": "#448361",
    "blue": "#337EA9",
    "purple": "#9065B0",
    "pink": "#C14C8A",
    "red": "#E03E3E",
}


def rich_plain(rich_texts: list[dict[str, Any]] | None) -> str:
    return "".join(rt.get("plain_text", "") for rt in (rich_texts or [])).strip()


def _color_style(annotations: dict[str, Any] | None) -> str:
    color = (annotations or {}).get("color") or "default"
    if color in {"", "default"}:
        return ""
    if color.endswith("_background"):
        return ""
    base = color.split("_")[0]
    hex_color = NOTION_TEXT_COLORS.get(color) or NOTION_TEXT_COLORS.get(base)
    return f' style="color:{hex_color}"' if hex_color else ""


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


def rich_text_to_html(
    rich_texts: list[dict[str, Any]] | None,
    *,
    resolve_title: Callable[[str], str] | None = None,
) -> str:
    parts: list[str] = []
    for rt in rich_texts or []:
        text = rt.get("plain_text") or ""
        if not text:
            continue
        ann = rt.get("annotations") or {}
        url = _hyperlink_url(rt)
        if url and rt.get("type") == "mention":
            plain = (rt.get("plain_text") or "").strip()
            if plain:
                text = plain
            elif resolve_title:
                mention = rt.get("mention") or {}
                pid = (mention.get("page") or {}).get("id")
                if pid:
                    try:
                        resolved = (resolve_title(pid) or "").strip()
                        if resolved:
                            text = resolved
                    except Exception:
                        pass
        escaped = html.escape(text, quote=False)
        if ann.get("code"):
            inner = f"<code>{escaped}</code>"
        else:
            inner = escaped
            if ann.get("bold"):
                inner = f"<strong>{inner}</strong>"
            if ann.get("italic"):
                inner = f"<em>{inner}</em>"
            if ann.get("strikethrough"):
                inner = f"<del>{inner}</del>"
            style = _color_style(ann)
            if style and inner == escaped:
                inner = f"<span{style}>{inner}</span>"
        if url:
            parts.append(
                f'<a href="{html.escape(url, quote=True)}" rel="noopener">{inner}</a>'
            )
        else:
            parts.append(inner)
    return "".join(parts)
