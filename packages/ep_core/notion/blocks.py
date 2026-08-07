"""Sérialisation des blocs Notion (contenu de page)."""

from __future__ import annotations

from typing import Any


def _rich_text_plain(rich: list[dict[str, Any]] | None) -> str:
    return "".join(rt.get("plain_text", "") for rt in (rich or []))


def serialize_block(block: dict[str, Any]) -> dict[str, Any]:
    """Bloc Notion simplifié, récursif via ``_children``."""
    btype = block.get("type") or "unsupported"
    data = block.get(btype) or {}

    out: dict[str, Any] = {
        "id": block.get("id"),
        "type": btype,
    }

    if "rich_text" in data:
        out["text"] = _rich_text_plain(data.get("rich_text"))
    if "caption" in data:
        out["caption"] = _rich_text_plain(data.get("caption"))
    if btype == "to_do":
        out["checked"] = bool(data.get("checked"))
    if btype in {"heading_1", "heading_2", "heading_3"}:
        out["is_toggleable"] = bool(data.get("is_toggleable"))
    if btype == "code":
        out["language"] = data.get("language") or ""
    if btype == "callout":
        out["icon"] = data.get("icon")
        out["color"] = data.get("color")
    if btype == "bookmark":
        out["url"] = data.get("url") or ""
    if btype == "image":
        img = data.get("file") or data.get("external") or {}
        out["url"] = img.get("url") or ""
    if btype == "table":
        out["table_width"] = data.get("table_width")
        out["has_column_header"] = data.get("has_column_header")
        out["has_row_header"] = data.get("has_row_header")

    children = block.get("_children") or []
    if children:
        out["children"] = [serialize_block(child) for child in children]

    return out


def serialize_block_tree(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [serialize_block(b) for b in blocks]
