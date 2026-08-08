"""Rendu HTML des fiches jurisprudence (aligné sur jurisprudence_docx)."""

from __future__ import annotations

import html
import json
import re
import unicodedata
from pathlib import Path
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


def _filter_key(value: str) -> str:
    return (value or "").strip().casefold()


def _build_formation_map(entries: list[dict]) -> dict[str, list[str]]:
    """Formations distinctes par juridiction (clé normalisée)."""
    out: dict[str, set[str]] = {}
    for entry in entries:
        j_key = entry.get("juridiction_key") or ""
        formation = (entry.get("formation") or "").strip()
        if not j_key or not formation:
            continue
        out.setdefault(j_key, set()).add(formation)
    return {key: sorted(values, key=str.casefold) for key, values in sorted(out.items())}


def _render_select(
    select_id: str,
    label: str,
    values: list[str],
    *,
    empty_label: str = "Toutes",
    collapsed: bool = False,
    disabled: bool = False,
) -> str:
    field_cls = "arrets-advanced-field"
    if collapsed:
        field_cls += " is-collapsed"
    attrs = f'id="{select_id}" aria-label="{html.escape(label)}"'
    if disabled:
        attrs += " disabled"
    lines = [
        f'<label class="{field_cls}" data-field="{html.escape(select_id)}">',
        f'<span class="arrets-advanced-label">{html.escape(label)}</span>',
        f"<select {attrs}>",
        f'<option value="">{html.escape(empty_label)}</option>',
    ]
    for value in values:
        lines.append(
            f'<option value="{html.escape(_filter_key(value), quote=True)}">'
            f"{html.escape(value)}</option>"
        )
    lines.append("</select></label>")
    return "\n".join(lines)


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
    site_root: Path | None = None,
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
    body_html = render_fiche_body(
        page,
        registry=registry,
        resolve_title=resolve_title,
        asset_prefix=asset_prefix,
    )
    linked_resources_html = ""
    if registry is not None:
        from .site_links import render_relation_extras

        linked_resources_html = render_relation_extras(
            props,
            registry,
            keys=("manuel", "index"),
            prefix=asset_prefix,
            resolve_title=resolve_title,
            site_root=site_root,
        )
    juridiction = prop_text(props, "Juridiction", "Jurisdiction")
    formation = prop_text(props, "Formation de jugement", "Formation")
    reference = prop_text(props, "Référence", "Reference")
    return {
        "title": title,
        "title_esc": html.escape(title),
        "slug": slugify(title),
        "theme": theme,
        "theme_key": _filter_key(theme),
        "juridiction": juridiction,
        "juridiction_key": _filter_key(juridiction),
        "formation": formation,
        "formation_key": _filter_key(formation),
        "reference": reference,
        "reference_key": _filter_key(reference),
        "date": _format_date(date_raw.split("→", 1)[0].strip()) if date_raw else "",
        "date_sort": date_sort,
        "date_year": date_sort[:4] if date_sort else "",
        "importance": prop_text(props, "Importance"),
        "body_html": body_html,
        "linked_resources_html": linked_resources_html,
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

    if not parts:
        return "<p class=\"arrets-empty\">Fiche en cours de rédaction.</p>"
    return "\n".join(parts)


def render_index_body(entries: list[dict]) -> tuple[str, str]:
    themes = sorted({e["theme"] for e in entries if e.get("theme")})
    juridictions = sorted(
        {e["juridiction"] for e in entries if e.get("juridiction")},
        key=str.casefold,
    )
    years = sorted(
        {e["date_year"] for e in entries if e.get("date_year")},
        reverse=True,
    )
    formation_map = _build_formation_map(entries)

    filters = ['<div class="arrets-filters">']
    filters.append('<div class="arrets-toolbar-row">')
    filters.append(
        '<label class="arrets-search-field" for="arrets-filter">'
        '<span class="sr-only">Filtrer</span>'
        '<input id="arrets-filter" type="search" placeholder="Rechercher un arrêt…" autocomplete="off">'
        "</label>"
    )
    if themes:
        filters.append('<div class="arrets-theme-field">')
        filters.append('<span class="arrets-theme-label">Thème :</span>')
        filters.append('<select id="arrets-theme" aria-label="Filtrer par thème">')
        filters.append('<option value="">Tous</option>')
        for th in themes:
            filters.append(
                f'<option value="{html.escape(_filter_key(th), quote=True)}">{html.escape(th)}</option>'
            )
        filters.append("</select></div>")
    filters.append(
        '<button type="button" class="arrets-advanced-toggle" id="arrets-advanced-toggle" '
        'aria-expanded="false" aria-controls="arrets-advanced-panel">Filtre avancé</button>'
    )
    filters.append("</div>")

    filters.append(
        '<div class="arrets-advanced-panel" id="arrets-advanced-panel" hidden>'
    )
    filters.append(
        '<div class="arrets-advanced-row" role="group" aria-label="Filtre avancé">'
    )
    filters.append(
        _render_select("arrets-juridiction", "Juridiction", juridictions, empty_label="Toutes")
    )
    filters.append(
        _render_select(
            "arrets-formation",
            "Formation de jugement",
            [],
            empty_label="Toutes",
            collapsed=True,
            disabled=True,
        )
    )
    filters.append(
        _render_select(
            "arrets-date-year",
            "Date",
            years,
            empty_label="Toutes les années",
        )
    )
    filters.append(
        '<label class="arrets-advanced-field" data-field="arrets-reference">'
        '<span class="arrets-advanced-label">Référence</span>'
        '<input id="arrets-reference" type="search" placeholder="n° requête, décision, RG…" '
        'autocomplete="off" aria-label="Filtrer par référence">'
        "</label>"
    )
    filters.append(
        '<label class="arrets-advanced-field" data-field="arrets-nom">'
        '<span class="arrets-advanced-label">Nom</span>'
        '<input id="arrets-nom" type="search" placeholder="Intitulé de l’arrêt…" '
        'autocomplete="off" aria-label="Filtrer par nom">'
        "</label>"
    )
    filters.append("</div></div>")
    filters.append(
        '<script type="application/json" id="arrets-formation-map">'
        f"{json.dumps(formation_map, ensure_ascii=False)}"
        "</script>"
    )
    filters.append("</div>")

    cards = ['<div class="arrets-list">']
    for e in entries:
        theme_attr = html.escape(e.get("theme_key") or "")
        cards.append(
            f'<a class="arrets-card" href="./{html.escape(e["slug"])}/" '
            f'data-term="{html.escape(_filter_key(e["title"]), quote=True)}" '
            f'data-theme="{theme_attr}" '
            f'data-juridiction="{html.escape(e.get("juridiction_key") or "", quote=True)}" '
            f'data-formation="{html.escape(e.get("formation_key") or "", quote=True)}" '
            f'data-date-year="{html.escape(e.get("date_year") or "", quote=True)}" '
            f'data-reference="{html.escape(e.get("reference_key") or "", quote=True)}" '
            f'data-nom="{html.escape(_filter_key(e["title"]), quote=True)}">'
            f'<p class="arrets-card-title">{html.escape(e["title"])}</p>'
        )
        meta_bits = [x for x in (e.get("date"), e.get("theme"), e.get("importance")) if x]
        if meta_bits:
            cards.append(f'<p class="arrets-card-meta">{" · ".join(html.escape(x) for x in meta_bits)}</p>')
        cards.append("</a>")
    cards.append("</div>")
    return "\n".join(filters), "\n".join(cards)


def render_arret_nav_link(entry: dict | None, *, kind: str) -> str:
    if entry is None:
        return ""
    label = "Fiche précédente" if kind == "prev" else "Fiche suivante"
    css = "manuel-chapternav-prev" if kind == "prev" else "manuel-chapternav-next"
    href = f'../{html.escape(entry["slug"], quote=True)}/'
    title = entry.get("title_esc") or html.escape(entry.get("title") or "")
    return (
        f'    <a class="{css}" href="{href}">'
        f"<span>{label}</span>{title}</a>"
    )


FILTER_JS = """
<script>
(function () {
  const input = document.getElementById("arrets-filter");
  const theme = document.getElementById("arrets-theme");
  const juridiction = document.getElementById("arrets-juridiction");
  const formation = document.getElementById("arrets-formation");
  const dateYear = document.getElementById("arrets-date-year");
  const reference = document.getElementById("arrets-reference");
  const nom = document.getElementById("arrets-nom");
  const formationField = document.querySelector('[data-field="arrets-formation"]');
  const advancedToggle = document.getElementById("arrets-advanced-toggle");
  const advancedPanel = document.getElementById("arrets-advanced-panel");
  const cards = Array.from(document.querySelectorAll(".arrets-card"));

  let formationMap = {};
  const mapEl = document.getElementById("arrets-formation-map");
  if (mapEl) {
    try {
      formationMap = JSON.parse(mapEl.textContent || "{}");
    } catch (_) {}
  }

  function norm(value) {
    return (value || "").trim().toLowerCase();
  }

  function updateFormation() {
    if (!formation) return;
    const jKey = norm(juridiction && juridiction.value);
    const options = formationMap[jKey] || [];
    formation.innerHTML = '<option value="">Toutes</option>';
    options.forEach((label) => {
      const opt = document.createElement("option");
      opt.value = norm(label);
      opt.textContent = label;
      formation.appendChild(opt);
    });
    const active = Boolean(jKey && options.length);
    formation.disabled = !active;
    const row = formationField && formationField.closest(".arrets-advanced-row");
    if (formationField) {
      formationField.classList.toggle("is-collapsed", !active);
    }
    if (row) {
      row.classList.toggle("has-formation", active);
    }
    if (!active) {
      formation.value = "";
    }
  }

  function apply() {
    const q = norm(input && input.value);
    const th = norm(theme && theme.value);
    const jv = norm(juridiction && juridiction.value);
    const fv = norm(formation && formation.value);
    const dy = norm(dateYear && dateYear.value);
    const rv = norm(reference && reference.value);
    const nv = norm(nom && nom.value);

    cards.forEach((el) => {
      const okQ = !q
        || norm(el.getAttribute("data-term")).includes(q)
        || norm(el.getAttribute("data-nom")).includes(q)
        || norm(el.textContent).includes(q);
      const okT = !th || norm(el.getAttribute("data-theme")) === th;
      const okJ = !jv || norm(el.getAttribute("data-juridiction")) === jv;
      const okF = !fv || norm(el.getAttribute("data-formation")) === fv;
      const okD = !dy || norm(el.getAttribute("data-date-year")) === dy;
      const okR = !rv || norm(el.getAttribute("data-reference")).includes(rv);
      const okN = !nv || norm(el.getAttribute("data-nom")).includes(nv);
      el.hidden = !(okQ && okT && okJ && okF && okD && okR && okN);
    });
  }

  function onChange(el, eventName) {
    if (!el) return;
    el.addEventListener(eventName, () => {
      if (el === juridiction) updateFormation();
      apply();
    });
  }

  onChange(input, "input");
  onChange(theme, "change");
  onChange(juridiction, "change");
  onChange(formation, "change");
  onChange(dateYear, "change");
  onChange(reference, "input");
  onChange(nom, "input");

  if (advancedToggle && advancedPanel) {
    advancedToggle.addEventListener("click", () => {
      const open = advancedPanel.hidden;
      advancedPanel.hidden = !open;
      advancedToggle.setAttribute("aria-expanded", open ? "true" : "false");
      advancedToggle.classList.toggle("is-open", open);
    });
  }

  updateFormation();
})();
</script>
"""
