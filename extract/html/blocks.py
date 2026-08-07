"""Rendu des blocs Notion → fragments HTML."""

from __future__ import annotations

from typing import Any, Callable

from .rich_text import rich_plain, rich_text_to_html

HEADING_TAGS = {
    "heading_1": "h2",
    "heading_2": "h3",
    "heading_3": "h4",
    "heading_4": "h5",
}


def is_empty_block(block: dict[str, Any]) -> bool:
    btype = block.get("type")
    if btype == "divider":
        return False
    if btype == "table_row":
        cells = (block.get("table_row") or {}).get("cells") or []
        return not cells
    children = block.get("_children") or []
    if rich_plain(_block_rich_text(block)):
        return False
    if not children:
        return True
    return all(is_empty_block(c) for c in children)


def _block_rich_text(block: dict[str, Any]) -> list[dict[str, Any]]:
    btype = block.get("type")
    data = block.get(btype) or {}
    if isinstance(data, dict):
        return data.get("rich_text") or []
    return []


class BlockRenderer:
    def __init__(self, *, resolve_title: Callable[[str], str] | None = None):
        self.resolve_title = resolve_title

    def render_blocks(self, blocks: list[dict[str, Any]]) -> str:
        return "".join(self._render_block(b) for b in blocks if not is_empty_block(b))

    def _render_block(self, block: dict[str, Any]) -> str:
        btype = block.get("type")
        data = block.get(btype) or {}
        children = block.get("_children") or []

        if btype == "column_list":
            inner = "".join(
                self.render_blocks(col.get("_children") or [])
                for col in children
                if col.get("type") == "column"
            )
            return f'<div class="column-list">{inner}</div>'

        if btype == "column":
            return f'<div class="column">{self.render_blocks(children)}</div>'

        if btype == "callout":
            rich = rich_text_to_html(
                data.get("rich_text") or [], resolve_title=self.resolve_title
            )
            body = self.render_blocks(children)
            lead = f"<p>{rich}</p>" if rich else ""
            return f'<aside class="encadre">{lead}{body}</aside>'

        if btype in HEADING_TAGS:
            tag = HEADING_TAGS[btype]
            inner = rich_text_to_html(
                data.get("rich_text") or [], resolve_title=self.resolve_title
            )
            nested = self.render_blocks(children)
            return f"<{tag}>{inner}</{tag}>{nested}"

        if btype == "quote":
            inner = rich_text_to_html(
                data.get("rich_text") or [], resolve_title=self.resolve_title
            )
            extra = "".join(
                self._render_block(c)
                for c in children
                if c.get("type") == "paragraph" or rich_plain(_block_rich_text(c))
            )
            return f"<blockquote><p>{inner}</p>{extra}</blockquote>"

        if btype == "bulleted_list_item":
            inner = rich_text_to_html(
                data.get("rich_text") or [], resolve_title=self.resolve_title
            )
            nested = self.render_blocks(children)
            return f"<ul><li>{inner}{nested}</li></ul>"

        if btype == "numbered_list_item":
            inner = rich_text_to_html(
                data.get("rich_text") or [], resolve_title=self.resolve_title
            )
            nested = self.render_blocks(children)
            return f"<ol><li>{inner}{nested}</li></ol>"

        if btype == "to_do":
            mark = "☑" if data.get("checked") else "☐"
            inner = rich_text_to_html(
                data.get("rich_text") or [], resolve_title=self.resolve_title
            )
            return f'<p class="todo">{mark} {inner}</p>'

        if btype == "toggle":
            summary = rich_text_to_html(
                data.get("rich_text") or [], resolve_title=self.resolve_title
            )
            body = self.render_blocks(children)
            if summary:
                return f"<details><summary>{summary}</summary>{body}</details>"
            return body

        if btype == "divider":
            return "<hr>"

        if btype == "table":
            return self._render_table(children)

        if btype == "synced_block":
            return self.render_blocks(children)

        if btype == "paragraph" or rich_plain(data.get("rich_text")):
            inner = rich_text_to_html(
                data.get("rich_text") or [], resolve_title=self.resolve_title
            )
            nested = self.render_blocks(children)
            return f"<p>{inner}</p>{nested}"

        if children:
            return self.render_blocks(children)
        return ""

    def _render_table(self, children: list[dict[str, Any]]) -> str:
        rows: list[list[list[dict[str, Any]]]] = []
        for row in children:
            if row.get("type") != "table_row":
                continue
            cells = (row.get("table_row") or {}).get("cells") or []
            rows.append(cells)
        if not rows:
            return ""
        n_cols = max(len(r) for r in rows)
        lines = ['<table class="notion-table">']
        for row in rows:
            lines.append("<tr>")
            for c_idx in range(n_cols):
                rich = row[c_idx] if c_idx < len(row) else []
                cell = rich_text_to_html(rich, resolve_title=self.resolve_title)
                lines.append(f"<td>{cell}</td>")
            lines.append("</tr>")
        lines.append("</table>")
        return "".join(lines)
