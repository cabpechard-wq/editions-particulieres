"""Arborescence DP-XXX du manuel (URLs, navigation, fil d'Ariane)."""

from __future__ import annotations

import html as html_mod
import re
from typing import Any

_RE_MANUEL = re.compile(r"^DP-(\d+)$", re.I)
_RE_ACTUALITE = re.compile(r"^DP-(\d+)[/ _](\d+)$", re.I)


def normalize_ref(ref: str) -> str:
    ref = (ref or "").strip()
    m = _RE_ACTUALITE.match(ref.replace("_", "/"))
    if m:
        return f"DP-{m.group(1)}/{m.group(2)}"
    m = _RE_MANUEL.match(ref)
    if m:
        return f"DP-{m.group(1)}"
    return ref


def is_actualite_ref(ref: str) -> bool:
    return bool(_RE_ACTUALITE.match((ref or "").strip().replace("_", "/")))


def manuel_digits(ref: str) -> str | None:
    m = _RE_MANUEL.match((ref or "").strip())
    if not m:
        return None
    return m.group(1)


def pad_digits(digits: str, width: int = 3) -> str:
    d = (digits or "").lstrip("0") or "0"
    if d == "0":
        return "0" * width
    return d.ljust(width, "0") if len(d) <= width else d


def parent_digits(digits: str) -> str | None:
    d = (digits or "").rstrip("0")
    if not d:
        return None
    parent_sig = d[:-1]
    if not parent_sig:
        return "000"
    width = max(3, len(digits))
    return parent_sig.ljust(width, "0")


def ancestor_chain(digits: str) -> list[str]:
    chain: list[str] = []
    cur: str | None = pad_digits(digits)
    seen: set[str] = set()
    while cur and cur not in seen:
        seen.add(cur)
        chain.append(cur)
        cur = parent_digits(cur)
    chain.reverse()
    return chain


def segment_for(digits: str) -> str:
    return f"dp-{digits.lower()}"


def path_segments_for(digits: str) -> list[str]:
    return [segment_for(d) for d in ancestor_chain(digits)]


def rel_between(from_segs: list[str], to_segs: list[str]) -> str:
    i = 0
    while i < len(from_segs) and i < len(to_segs) and from_segs[i] == to_segs[i]:
        i += 1
    up = "../" * (len(from_segs) - i)
    down = "/".join(to_segs[i:])
    if down:
        return f"{up}{down}/"
    return up or "./"


def asset_prefix(depth: int) -> str:
    return "../" * (depth + 1)


def sort_key_ref(ref: str) -> tuple:
    parts = re.split(r"(\d+)", (ref or "").strip())
    key: list = []
    for p in parts:
        if not p:
            continue
        if p.isdigit():
            key.append((0, int(p)))
        else:
            key.append((1, p.casefold()))
    return tuple(key)


def effective_parent(digits: str, by_digits: dict[str, dict[str, Any]]) -> str | None:
    p = parent_digits(digits)
    while p is not None and p not in by_digits:
        p = parent_digits(p)
    return p


def build_nav_tree_html(
    chapters: list[dict[str, Any]],
    *,
    from_segs: list[str] | None,
    current_digits: str | None = None,
    skip_root: bool = False,
) -> str:
    by_digits = {ch["digits"]: ch for ch in chapters}
    children: dict[str | None, list[dict[str, Any]]] = {}
    for ch in chapters:
        p = effective_parent(ch["digits"], by_digits)
        children.setdefault(p, []).append(ch)
    for kids in children.values():
        kids.sort(key=lambda c: sort_key_ref(c["ref"]))

    def href_for(ch: dict[str, Any]) -> str:
        if from_segs is None:
            return "./" + "/".join(ch["segments"]) + "/"
        return rel_between(from_segs, ch["segments"])

    def render(parent: str | None) -> str:
        kids = children.get(parent) or []
        if not kids:
            return ""
        lines = ["<ul>"]
        for ch in kids:
            active = ch["digits"] == current_digits
            cls = ' class="is-current"' if active else ""
            lines.append(
                f"<li{cls}>"
                f'<a href="{href_for(ch)}">'
                f'<span class="nav-title">{ch["title_esc"]}</span>'
                f"</a>"
            )
            nested = render(ch["digits"])
            if nested:
                lines.append(nested)
            lines.append("</li>")
        lines.append("</ul>")
        return "\n".join(lines)

    roots = children.get(None) or []
    if skip_root and len(roots) == 1:
        return render(roots[0]["digits"])
    return render(None)


def build_breadcrumb_html(chapter: dict[str, Any], by_digits: dict[str, dict[str, Any]]) -> str:
    prefix = asset_prefix(len(chapter["segments"]))
    bits = [
        f'<a href="{prefix}index.html">Droit public et administratif</a>',
        '<span class="sep">›</span>',
        f'<a href="{prefix}bibliotheque/">Bibliothèque universitaire</a>',
        '<span class="sep">›</span>',
        f'<a href="{rel_between(chapter["segments"], [])}">Manuel</a>',
    ]
    for dig in chapter["ancestors"]:
        ch = by_digits.get(dig)
        if not ch:
            continue
        if dig == chapter["digits"]:
            bits.append('<span class="sep">›</span>')
            bits.append(f"<strong>{ch['title_esc']}</strong>")
        else:
            href = rel_between(chapter["segments"], ch["segments"])
            bits.append('<span class="sep">›</span>')
            bits.append(f'<a href="{href}">{ch["title_esc"]}</a>')
    return "\n    ".join(bits)


def render_chapter_link(
    chapter: dict[str, Any] | None,
    *,
    kind: str,
    from_segs: list[str],
) -> str:
    if chapter is None:
        return ""
    label = "Chapitre précédent" if kind == "prev" else "Chapitre suivant"
    css = "manuel-chapternav-prev" if kind == "prev" else "manuel-chapternav-next"
    href = rel_between(from_segs, chapter["segments"])
    return (
        f'    <a class="{css}" href="{href}">'
        f"<span>{label}</span>{chapter['title_esc']}</a>"
    )


def classify_chapter(
    *,
    title: str,
    ref: str,
    body: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    """Retourne (chapitre_manuel, fiche_actualité, message_skip)."""
    import re as _re

    raw_ref = (ref or "").strip()
    ref_norm = normalize_ref(raw_ref) if raw_ref else ""

    if is_actualite_ref(raw_ref or ref_norm):
        safe = _re.sub(r"[^a-zA-Z0-9]+", "-", (raw_ref or ref_norm).lower()).strip("-")
        aside = {
            "title": title,
            "title_esc": html_mod.escape(title),
            "ref": normalize_ref(raw_ref or ref_norm),
            "ref_esc": html_mod.escape(normalize_ref(raw_ref or ref_norm)),
            "slug": safe or "fiche",
            "body": body,
        }
        return None, aside, None

    digits = manuel_digits(ref_norm)
    if not digits:
        return None, None, f"réf. hors schéma DP-XXX : {raw_ref!r} ({title})"

    digits = pad_digits(digits)
    segs = path_segments_for(digits)
    chapter = {
        "title": title,
        "title_esc": html_mod.escape(title),
        "ref": f"DP-{digits}",
        "ref_esc": html_mod.escape(f"DP-{digits}"),
        "digits": digits,
        "ancestors": ancestor_chain(digits),
        "segments": segs,
        "depth": len(segs),
        "body": body,
    }
    return chapter, None, None
