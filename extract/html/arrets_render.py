"""Rendu HTML des fiches jurisprudence (aligné sur jurisprudence_docx)."""

from __future__ import annotations

import html
import re
import unicodedata
from typing import Any

from packages.ep_core.notion import page_title, property_plain

FICHE_FIELDS = ("Faits", "Enjeu juridique", "Solution", "Perspective")
CONSIDERANT_NAMES = ("Considérant de principe", "Considerant de principe")
_DATE_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def _norm(name: str) -> str:
    return (name or "").strip().casefold()


def _prop_by_name(props: dict[str, Any], *names: str) -> tuple[str, Any] | None:
    lower = {_norm(k): k for k in props}
    for name in names:
        key = lower.get(_norm(name))
        if key:
            return key, props[key]
    return None


def prop_text(props: dict[str, Any], *names: str) -> str:
    found = _prop_by_name(props, *names)
    if not found:
        return ""
    raw = found[1]
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, dict) and raw.get("type"):
        return property_plain(raw).strip()
    if raw is None:
        return ""
    return str(raw).strip()


def title_from_page(page: dict[str, Any]) -> str:
    props = page.get("properties") or {}
    return prop_text(props, "Nom") or page_title(page) or "Sans titre"


def slugify(term: str) -> str:
    s = unicodedata.normalize("NFKD", term)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "arret"


def _format_date(raw: str) -> str:
    m = _DATE_PREFIX.match((raw or "").strip().split("→", 1)[0].strip())
    if m:
        y, mo, d = m.group(1).split("-")
        return f"{d}/{mo}/{y}"
    return (raw or "").strip()


def _format_reference(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    if raw.lower().startswith("n"):
        return raw
    if re.fullmatch(r"\d+", raw):
        return f"n° {raw}"
    return raw


def meta_line(props: dict[str, Any]) -> str:
    bits: list[str] = []
    for names in (
        ("Juridiction", "Jurisdiction"),
        ("Formation de jugement", "Formation"),
        ("Date",),
        ("Référence", "Reference"),
    ):
        text = prop_text(props, *names)
        if not text:
            continue
        if _norm(names[0]) == "date":
            text = _format_date(text)
        elif _norm(names[0]) == "référence":
            text = _format_reference(text)
        bits.append(text)
    return ", ".join(bits)


def _dedupe_slugs(entries: list[dict]) -> None:
    seen: dict[str, int] = {}
    for e in entries:
        base = e["slug"]
        n = seen.get(base, 0)
        seen[base] = n + 1
        if n:
            e["slug"] = f"{base}-{n + 1}"


def entry_from_page(
    page: dict[str, Any],
    *,
    registry=None,
    resolve_title=None,
    asset_prefix: str = "../../",
) -> dict[str, Any] | None:
    props = page.get("properties") or {}
    title = title_from_page(page)
    if not title or title == "Sans titre":
        return None
    theme = prop_text(props, "Thème", "Theme")
    date_raw = prop_text(props, "Date")
    date_sort = ""
    if date_raw:
        head = date_raw.strip().split("→", 1)[0].strip()
        m = _DATE_PREFIX.match(head)
        if m:
            date_sort = m.group(1)
    return {
        "title": title,
        "slug": slugify(title),
        "theme": theme,
        "date": _format_date(date_raw.split("→", 1)[0].strip()) if date_raw else "",
        "date_sort": date_sort,
        "importance": prop_text(props, "Importance"),
        "body_html": render_fiche_body(
            page,
            registry=registry,
            resolve_title=resolve_title,
            asset_prefix=asset_prefix,
        ),
    }


def render_fiche_body(
    page: dict[str, Any],
    *,
    registry=None,
    resolve_title=None,
    asset_prefix: str = "../../",
) -> str:
    props = page.get("properties") or {}
    parts: list[str] = []

    objet = prop_text(props, "Objet")
    if objet:
        parts.append(f'<p class="arrets-objet"><strong>{html.escape(objet)}</strong></p>')

    portee = prop_text(props, "Portée", "Portee")
    if portee:
        parts.append(f'<p class="arrets-portee">{html.escape(portee)}</p>')

    found = _prop_by_name(props, *CONSIDERANT_NAMES)
    if found:
        label, _ = found
        text = prop_text(props, label)
        if text:
            parts.append(f"<blockquote><p>{html.escape(text)}</p></blockquote>")

    meta = meta_line(props)
    fiche_items = [(k, prop_text(props, k)) for k in FICHE_FIELDS]
    fiche_items = [(k, t) for k, t in fiche_items if t]
    if meta or fiche_items:
        box = ['<aside class="fiche-decision">', '<p class="fiche-decision-title">Fiche de décision</p>']
        if meta:
            box.append(f'<p class="fiche-decision-meta"><em>{html.escape(meta)}</em></p>')
        for label, text in fiche_items:
            box.append(
                f"<p><strong>{html.escape(label)}.</strong> {html.escape(text)}</p>"
            )
        box.append("</aside>")
        parts.append("\n".join(box))

    if registry is not None:
        from .site_links import render_relation_extras

        extras = render_relation_extras(
            props,
            registry,
            keys=("manuel", "index"),
            prefix=asset_prefix,
            resolve_title=resolve_title,
        )
        if extras:
            parts.append(extras)

    if not parts:
        return "<p class=\"arrets-empty\">Fiche en cours de rédaction.</p>"
    return "\n".join(parts)


def render_index_body(entries: list[dict]) -> tuple[str, str]:
    themes = sorted({e["theme"] for e in entries if e.get("theme")})
    filters = ['<p class="arrets-toolbar">']
    filters.append(
        '<label class="sr-only" for="arrets-filter">Filtrer</label>'
        '<input id="arrets-filter" type="search" placeholder="Rechercher un arrêt…" autocomplete="off">'
    )
    if themes:
        filters.append('<span class="arrets-theme-label">Thème :</span>')
        filters.append('<select id="arrets-theme" aria-label="Filtrer par thème">')
        filters.append('<option value="">Tous</option>')
        for th in themes:
            filters.append(
                f'<option value="{html.escape(th.lower(), quote=True)}">{html.escape(th)}</option>'
            )
        filters.append("</select>")
    filters.append("</p>")

    cards = ['<div class="arrets-list">']
    for e in entries:
        theme_attr = html.escape((e.get("theme") or "").lower())
        cards.append(
            f'<a class="arrets-card" href="./{html.escape(e["slug"])}/" '
            f'data-term="{html.escape(e["title"].lower())}" data-theme="{theme_attr}">'
            f'<p class="arrets-card-title">{html.escape(e["title"])}</p>'
        )
        meta_bits = [x for x in (e.get("date"), e.get("theme"), e.get("importance")) if x]
        if meta_bits:
            cards.append(f'<p class="arrets-card-meta">{" · ".join(html.escape(x) for x in meta_bits)}</p>')
        cards.append("</a>")
    cards.append("</div>")
    return "\n".join(filters), "\n".join(cards)


FILTER_JS = """
<script>
(function () {
  const input = document.getElementById("arrets-filter");
  const theme = document.getElementById("arrets-theme");
  const cards = Array.from(document.querySelectorAll(".arrets-card"));
  function apply() {
    const q = (input && input.value || "").trim().toLowerCase();
    const th = (theme && theme.value || "").trim().toLowerCase();
    cards.forEach((el) => {
      const okQ = !q || (el.getAttribute("data-term") || "").includes(q)
        || (el.textContent || "").toLowerCase().includes(q);
      const okT = !th || (el.getAttribute("data-theme") || "") === th;
      el.hidden = !(okQ && okT);
    });
  }
  if (input) input.addEventListener("input", apply);
  if (theme) theme.addEventListener("change", apply);
})();
</script>
"""
