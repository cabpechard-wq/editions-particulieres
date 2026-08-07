"""Sérialisation des propriétés Notion → JSON."""

from __future__ import annotations

from typing import Any

from .ids import page_url_from_id


def page_title(page: dict[str, Any]) -> str:
    props = page.get("properties") or {}
    for prop in props.values():
        if prop.get("type") == "title":
            parts = prop.get("title") or []
            text = "".join(p.get("plain_text", "") for p in parts).strip()
            if text:
                return text
    return page.get("id", "sans-titre")


def property_to_json(prop: dict[str, Any]) -> Any:
    """Valeur JSON-serializable d'une propriété Notion."""
    t = prop.get("type")
    if not t:
        return None
    val = prop.get(t)

    if t == "title":
        return "".join(x.get("plain_text", "") for x in (val or []))
    if t in {"rich_text", "text"}:
        return "".join(x.get("plain_text", "") for x in (val or []))
    if t in {"select", "status"}:
        return (val or {}).get("name") or ""
    if t == "multi_select":
        return [x.get("name", "") for x in (val or []) if x.get("name")]
    if t == "date":
        if not val:
            return None
        return {
            "start": val.get("start") or "",
            "end": val.get("end") or "",
            "time_zone": val.get("time_zone"),
        }
    if t == "number":
        return val
    if t == "checkbox":
        return bool(val)
    if t in {"url", "email", "phone_number"}:
        return val or ""
    if t == "people":
        return [
            {"id": p.get("id"), "name": p.get("name") or ""}
            for p in (val or [])
            if p.get("id")
        ]
    if t == "relation":
        return [
            {"id": r["id"], "url": page_url_from_id(r["id"])}
            for r in (val or [])
            if r.get("id")
        ]
    if t == "formula":
        if not val:
            return None
        ft = val.get("type")
        return val.get(ft)
    if t == "rollup":
        if not val:
            return None
        rt = val.get("type")
        if rt == "array":
            return [
                property_to_json({"type": item.get("type"), item.get("type"): item.get(item.get("type"))})
                for item in (val.get("array") or [])
            ]
        if rt == "number":
            return val.get("number")
        if rt == "date":
            return property_to_json({"type": "date", "date": val.get("date")})
        return None
    if t == "unique_id":
        if not val:
            return None
        prefix = val.get("prefix") or ""
        num = val.get("number")
        return f"{prefix}-{num}" if prefix else num
    if t == "files":
        out = []
        for f in val or []:
            name = f.get("name") or ""
            url = ""
            if f.get("type") == "external":
                url = (f.get("external") or {}).get("url") or ""
            elif f.get("type") == "file":
                url = (f.get("file") or {}).get("url") or ""
            out.append({"name": name, "url": url})
        return out
    if t in {"created_time", "last_edited_time"}:
        return val or ""
    if t in {"created_by", "last_edited_by"}:
        return {"id": (val or {}).get("id"), "name": (val or {}).get("name") or ""}
    return None


def extract_page_properties(
    page: dict[str, Any],
    *,
    exclude: set[str] | None = None,
) -> dict[str, Any]:
    """Toutes les propriétés d'une page, sauf celles exclues."""
    exclude = {n.casefold() for n in (exclude or set())}
    props = page.get("properties") or {}
    out: dict[str, Any] = {}
    for name, prop in props.items():
        if name.casefold() in exclude:
            continue
        out[name] = property_to_json(prop)
    return out


def property_plain(prop: dict[str, Any]) -> str:
    """Texte lisible d'une propriété Notion brute (API)."""
    t = prop.get("type")
    if not t:
        return ""
    val = prop.get(t)

    if t == "title":
        return "".join(x.get("plain_text", "") for x in (val or []))
    if t in {"rich_text", "text"}:
        return "".join(x.get("plain_text", "") for x in (val or []))
    if t in {"select", "status"}:
        return (val or {}).get("name") or ""
    if t == "multi_select":
        return ", ".join(x.get("name", "") for x in (val or []) if x.get("name"))
    if t == "date":
        if not val:
            return ""
        start = val.get("start") or ""
        end = val.get("end")
        return f"{start} → {end}" if end else start
    if t == "number":
        return "" if val is None else str(val)
    if t == "checkbox":
        return "Oui" if val else "Non"
    if t in {"url", "email", "phone_number"}:
        return val or ""
    if t == "relation":
        return ", ".join(r.get("id", "") for r in (val or []) if r.get("id"))
    if t == "formula":
        if not val:
            return ""
        ft = val.get("type")
        fv = val.get(ft)
        return "" if fv is None else str(fv)
    return ""
