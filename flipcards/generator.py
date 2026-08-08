"""Génère des flipcards HTML (style Quizlet) et un JSON mobile (recto=Nom, verso=Verso)."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

FLIPCARDS_DIR = Path(__file__).resolve().parent
DEFAULT_MATRICE = FLIPCARDS_DIR / "matrices" / "flipcards_matrice.csv"
COLORS_PATH = FLIPCARDS_DIR / "matrices" / "classifier_colors.json"
MATRICE_JSON = FLIPCARDS_DIR / "matrices" / "flipcards_matrice.json"

# Noms de couleur Notion API → jetons CSS (data-color)
NOTION_COLOR_NAMES = (
    "default",
    "gray",
    "brown",
    "orange",
    "yellow",
    "green",
    "blue",
    "purple",
    "pink",
    "red",
)


def sanitize_filename(title: str, max_len: int = 120) -> str:
    title = (title or "sans-titre").strip()
    title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title)
    title = re.sub(r"\s+", " ", title).strip(" .")
    if not title:
        title = "sans-titre"
    return title[:max_len]


def _get(row: dict[str, str], *keys: str) -> str:
    for k in keys:
        v = (row.get(k) or "").strip()
        if v:
            return v
    return ""


def _split_tags(raw: str) -> list[str]:
    """Sépare multi-select Notion (« a, b ») en liste de tags."""
    return [p.strip() for p in (raw or "").split(",") if p.strip()]


def format_theme_label(raw: str) -> str:
    """Enlève le préfixe numérique « 41-… » d'un thème Notion."""
    bit = (raw or "").strip()
    if not bit:
        return ""
    m = re.match(r"^\d+\s*[-–—]\s*(.+)$", bit)
    return (m.group(1).strip() if m else bit)


def split_themes(raw: str) -> list[str]:
    """Liste de thèmes normalisés (sans préfixe numérique), dédupliqués."""
    seen: set[str] = set()
    out: list[str] = []
    for bit in _split_tags(raw):
        label = format_theme_label(bit)
        key = label.casefold()
        if not label or key in seen:
            continue
        seen.add(key)
        out.append(label)
    return out


def importance_level(raw: str) -> int:
    """Nombre d'étoiles (1–4) depuis la propriété Notion Importance."""
    s = (raw or "").strip()
    if not s:
        return 0
    n = s.count("⭐") or s.count("★") or s.count("*")
    if n:
        return min(4, max(1, n))
    m = re.search(r"[1-4]", s)
    return int(m.group(0)) if m else 0


def card_payload(row: dict[str, str]) -> dict:
    """Objet carte normalisé pour JSON mobile / HTML."""
    themes = split_themes(_get(row, "Thème"))
    notions = _split_tags(_get(row, "Notions"))
    imp_raw = _get(row, "Importance")
    level = importance_level(imp_raw)
    return {
        "id": _get(row, "id"),
        "recto": _get(row, "Nom", "title"),
        "verso": _get(row, "Verso"),
        "url": _get(row, "url"),
        "date": _get(row, "Date"),
        "juridiction": _get(row, "Juridiction"),
        "formation": _get(row, "Formation de jugement"),
        "titre": _get(row, "Titre de la décision"),
        "reference": _get(row, "Référence"),
        "importance": imp_raw,
        "importance_level": level,
        "theme": ", ".join(themes),
        "theme_raw": _get(row, "Thème"),
        "themes": themes,
        "notions": notions,
        "objet": _get(row, "Objet"),
        "portee": _get(row, "Portée"),
        "considerant": _get(row, "Considérant de principe"),
        "faits": _get(row, "Faits"),
        "enjeu": _get(row, "Enjeu juridique", "Enjeu"),
        "solution": _get(row, "Solution"),
        "perspective": _get(row, "Perspective", "Perspectives"),
    }


def _unique_sorted(values: list[str]) -> list[str]:
    return sorted(set(values), key=lambda s: s.casefold())


def classifiers_catalog(cards: list[dict]) -> dict[str, list[str]]:
    themes: list[str] = []
    notions: list[str] = []
    for c in cards:
        themes.extend(c.get("themes") or [])
        notions.extend(c.get("notions") or [])
    return {
        "themes": _unique_sorted(themes),
        "notions": _unique_sorted(notions),
    }


def _normalize_color_name(raw: str | None) -> str:
    name = (raw or "default").strip().lower()
    return name if name in NOTION_COLOR_NAMES else "default"


def load_classifier_colors(
    colors: dict[str, dict[str, str]] | None = None,
) -> dict[str, dict[str, str]]:
    """Charge les couleurs d'options Notion (Thème / Notions)."""
    if colors is not None:
        return {
            "themes": {
                k: _normalize_color_name(v)
                for k, v in (colors.get("themes") or {}).items()
            },
            "notions": {
                k: _normalize_color_name(v)
                for k, v in (colors.get("notions") or {}).items()
            },
        }

    for path in (COLORS_PATH, MATRICE_JSON):
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        blob = data.get("classifier_colors") if "classifier_colors" in data else data
        if not isinstance(blob, dict):
            continue
        themes = blob.get("themes") or {}
        notions = blob.get("notions") or {}
        if themes or notions:
            return load_classifier_colors(
                {"themes": dict(themes), "notions": dict(notions)}
            )

    return {"themes": {}, "notions": {}}


def color_for_label(
    label: str,
    *,
    group: str,
    colors: dict[str, dict[str, str]],
) -> str:
    key = "themes" if group == "theme" else "notions"
    mapping = colors.get(key) or {}
    bit = (label or "").strip()
    if not bit:
        return "default"
    if bit in mapping:
        return _normalize_color_name(mapping[bit])
    # Thèmes : tenter aussi le libellé brut avec préfixe numérique
    if group == "theme":
        for raw, color in mapping.items():
            if format_theme_label(raw) == bit:
                return _normalize_color_name(color)
    return "default"


def rows_to_cards(rows: list[dict[str, str]]) -> list[dict]:
    cards = [card_payload(r) for r in rows]
    return [c for c in cards if c["recto"]]


def write_json(
    rows: list[dict[str, str]],
    out_path: Path,
    *,
    colors: dict[str, dict[str, str]] | None = None,
) -> Path:
    cards = rows_to_cards(rows)
    color_map = load_classifier_colors(colors)
    payload = {
        "kind": "flipcards",
        "count": len(cards),
        "recto_field": "Nom",
        "verso_field": "Verso",
        "classifiers": {
            "theme_field": "Thème",
            "notions_field": "Notions",
            **classifiers_catalog(cards),
        },
        "classifier_colors": color_map,
        "cards": cards,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out_path


def _esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def _tags_html(
    labels: list[str],
    *,
    css: str,
    group: str,
    colors: dict[str, dict[str, str]],
) -> str:
    if not labels:
        return ""
    chips = "".join(
        f'<span class="tag {css}" data-color="{_esc(color_for_label(t, group=group, colors=colors))}">{_esc(t)}</span>'
        for t in labels
    )
    return f'<div class="tags">{chips}</div>'


def _terms_list_html(
    cards: list[dict],
    *,
    colors: dict[str, dict[str, str]],
) -> str:
    items = []
    for idx, c in enumerate(cards):
        verso = _esc(c.get("verso") or "—")
        tags = _tags_html(
            c.get("themes") or [],
            css="tag-theme",
            group="theme",
            colors=colors,
        ) + _tags_html(
            c.get("notions") or [],
            css="tag-notion",
            group="notion",
            colors=colors,
        )
        items.append(
            f"""<li class="term-row" data-idx="{idx}" data-themes="{_esc(','.join(c.get('themes') or []))}" data-notions="{_esc(','.join(c.get('notions') or []))}">
  <div class="term-recto">{_esc(c["recto"])}{tags}</div>
  <div class="term-verso">{verso}</div>
</li>"""
        )
    return "\n".join(items)


def _importance_chips_html() -> str:
    bits = []
    for level in range(1, 5):
        label = "★" * level
        bits.append(
            f'<button type="button" class="chip chip-importance" data-group="importance" '
            f'data-value="{level}" aria-pressed="false" '
            f'title="{level} étoile{"s" if level > 1 else ""}">{label}</button>'
        )
    return "\n".join(bits)


def _stars_html(level: int) -> str:
    n = max(0, min(4, int(level or 0)))
    if not n:
        return ""
    return f'<span class="stars" aria-label="{n} étoile{"s" if n > 1 else ""}">{"★" * n}</span>'


def _chip_buttons_html(
    values: list[str],
    *,
    group: str,
    colors: dict[str, dict[str, str]],
) -> str:
    if not values:
        return '<p class="chips-empty">Aucun classificateur renseigné.</p>'
    bits = []
    for v in values:
        color = color_for_label(v, group=group, colors=colors)
        bits.append(
            f'<button type="button" class="chip" data-group="{_esc(group)}" '
            f'data-value="{_esc(v)}" data-color="{_esc(color)}" '
            f'aria-pressed="false">{_esc(v)}</button>'
        )
    return "\n".join(bits)


def _notion_color_css() -> str:
    """Capsules : fond blanc / texte gris ; bordure teintée ; hover + sélection = teinte vive."""
    # (bordure repos, teinte vive = hover bordure + sélection fond/bordure)
    palette = {
        "default": ("#d1d5db", "#4b5563"),
        "gray": ("#d1d5db", "#4b5563"),
        "brown": ("#d4a574", "#9a5b3a"),
        "orange": ("#fdba74", "#ea580c"),
        "yellow": ("#facc15", "#ca8a04"),
        "green": ("#009900", "#009900"),
        "blue": ("#93c5fd", "#2563eb"),
        "purple": ("#d8b4fe", "#9333ea"),
        "pink": ("#f9a8d4", "#db2777"),
        "red": ("#fca5a5", "#dc2626"),
    }
    rules: list[str] = []
    for name, (border, vivid) in palette.items():
        rules.append(
            f""".chip[data-color="{name}"], .tag[data-color="{name}"] {{
  --chip-border: {border}; --chip-vivid: {vivid};
}}"""
        )
    rules.append(
        """
.chip[data-color] {
  background: var(--bg-elevated);
  border-color: var(--chip-border);
  color: var(--muted);
}
.chip[data-color]:hover:not(:disabled):not(.is-disabled):not(.is-exclusive-dim):not([aria-pressed="true"]) {
  background: var(--bg-elevated);
  border-color: var(--chip-vivid);
  color: var(--chip-vivid);
}
.chip[data-color][aria-pressed="true"],
.chip[data-color][aria-pressed="true"]:hover {
  background: var(--chip-vivid);
  border-color: var(--chip-vivid);
  color: #0e1419;
}
.chip[data-color].is-disabled,
.chip[data-color]:disabled,
.chip[data-color].is-exclusive-dim:not([aria-pressed="true"]) {
  background: var(--bg-elevated);
  border-color: var(--chip-border);
  color: var(--muted);
  opacity: .28;
}
.tag[data-color] {
  background: var(--bg);
  border: 1px solid var(--chip-border);
  color: var(--muted);
  border-radius: 999px;
}
"""
    )
    return "\n".join(rules)


DEFAULT_PAGE_TITLE = "Grands arrêts du droit public et administratif"


def _cards_embed_json(cards: list[dict]) -> str:
    return json.dumps(
        [
            {
                "recto": c["recto"],
                "verso": c.get("verso") or "",
                "themes": c.get("themes") or [],
                "notions": c.get("notions") or [],
                "importance": c.get("importance") or "",
                "importance_level": c.get("importance_level") or 0,
                "objet": c.get("objet") or "",
                "portee": c.get("portee") or "",
                "considerant": c.get("considerant") or "",
                "faits": c.get("faits") or "",
                "enjeu": c.get("enjeu") or "",
                "solution": c.get("solution") or "",
                "perspective": c.get("perspective") or "",
            }
            for c in cards
        ],
        ensure_ascii=False,
    )


def build_html_document(
    rows: list[dict[str, str]],
    *,
    title: str = DEFAULT_PAGE_TITLE,
    colors: dict[str, dict[str, str]] | None = None,
    classifier_rows: list[dict[str, str]] | None = None,
    aside_rows: list[dict[str, str]] | None = None,
    demo_upsell: bool = False,
) -> str:
    cards = rows_to_cards(rows)
    # Catalogue des chips : jeu complet (ex. démo) ou limité aux cartes affichées
    catalog_cards = (
        rows_to_cards(classifier_rows) if classifier_rows is not None else cards
    )
    catalog = classifiers_catalog(catalog_cards)
    color_map = load_classifier_colors(colors)
    cards_json = _cards_embed_json(cards)
    # Pool dédié « 3 au hasard » (ex. démo : 15 fiches hors lot d'étude)
    aside_cards = rows_to_cards(aside_rows) if aside_rows else []
    aside_json = _cards_embed_json(aside_cards) if aside_cards else "[]"
    terms = _terms_list_html(
        aside_cards if aside_cards else cards, colors=color_map
    )
    theme_chips = _chip_buttons_html(
        catalog["themes"], group="theme", colors=color_map
    )
    notion_chips = _chip_buttons_html(
        catalog["notions"], group="notion", colors=color_map
    )
    importance_chips = _importance_chips_html()
    n = len(cards)
    color_css = _notion_color_css()
    demo_upsell_html = (
        '<p class="demo-upsell">'
        '<a class="demo-upsell-link" href="../checkout/">'
        "Accès à tout le jeu de cartes et aux ressources du site…"
        "</a></p>"
        if demo_upsell
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{_esc(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link id="theme-fonts" rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap">
<link id="theme-css" rel="stylesheet" href="../site.css">
<style>
/* Flipcards — la charte (couleurs, polices) vient de site.css / themes/ via site-theme.js */
:root {{
  --card-verso: var(--bg-elevated);
  --brass: var(--accent);
}}
* {{ box-sizing: border-box; }}
html, body {{
  margin: 0; min-height: 100%;
  color: var(--ink);
  font-family: var(--font-ui);
}}
body {{
  padding: 0 0 3.5rem;
}}
.wrap {{ max-width: 48rem; margin: 0 auto; padding: 1.5rem 1rem 0; }}
.wrap.is-study {{ max-width: 36rem; }}
.screen[hidden] {{ display: none !important; }}
:fullscreen .site-nav,
:-webkit-full-screen .site-nav {{ display: none !important; }}
:fullscreen body,
:-webkit-full-screen body {{ padding-bottom: 1.5rem; }}
:fullscreen .wrap,
:-webkit-full-screen .wrap {{ padding-top: 1.5rem; }}
.page-title {{
  margin: 0 0 .4rem;
  font-family: var(--font-display);
  font-size: clamp(1.7rem, 4vw, 2.2rem);
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1.15;
}}
.page-sub {{
  margin: 0 0 1.5rem;
  color: var(--muted); font-size: .95rem; line-height: 1.5;
}}
.home-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: .15rem 1.1rem 1.1rem;
}}
.classifier + .classifier {{ border-top: 1px solid var(--border); }}
.classifier-row {{
  display: flex; align-items: center; gap: .75rem; min-height: 3rem;
}}
.classifier-toggle {{
  appearance: none; border: 0; background: none; padding: 0;
  display: flex; align-items: center; gap: .6rem;
  cursor: pointer; color: inherit; font: inherit; min-width: 0;
}}
.classifier-title {{
  margin: 0; font-size: 1rem; font-weight: 700; color: var(--ink);
}}
.classifier-hint {{
  font-size: .72rem;
  font-weight: 500;
  color: var(--muted);
  letter-spacing: 0;
}}
.classifier-chevron {{
  width: 1rem; height: 1rem; color: var(--ink); flex: 0 0 auto;
  transition: transform .35s cubic-bezier(.2,.8,.2,1);
}}
.classifier.is-open .classifier-chevron {{ transform: rotate(180deg); }}
.classifier-clear {{
  appearance: none; border: 0; background: none; padding: 0;
  margin-left: auto; color: var(--muted);
  font: 500 .82rem var(--font-ui); cursor: pointer; white-space: nowrap;
}}
.classifier-clear:hover {{ color: var(--accent); }}
.classifier-slide {{ height: 0; overflow: hidden; }}
.classifier-slide-inner {{ min-height: 0; }}
.classifier-body {{ padding: 0 0 1rem 1.5rem; }}
.chips {{ display: flex; flex-wrap: wrap; gap: .4rem; }}
.chips-empty {{ margin: 0; color: var(--muted); font-size: .9rem; }}
.chip {{
  appearance: none; border: 1px solid var(--border);
  background: var(--bg-elevated); color: var(--muted);
  border-radius: 999px; padding: .4rem .85rem;
  font: 600 .78rem var(--font-ui); cursor: pointer;
  transition: background .15s, border-color .15s, color .15s;
}}
.chip:hover {{ border-color: var(--accent); color: var(--accent); }}
.chip[aria-pressed="true"] {{
  background: var(--accent); border-color: var(--accent); color: var(--bg);
}}
.chip.is-disabled, .chip:disabled {{
  opacity: .28; cursor: not-allowed; pointer-events: none;
  background: var(--bg-elevated); color: var(--muted);
}}
.chip.is-exclusive-dim:not([aria-pressed="true"]) {{
  opacity: .28;
  background: var(--bg-elevated);
  color: var(--muted);
}}
.chip.is-exclusive-dim:hover:not(:disabled):not(.is-disabled) {{
  opacity: .55;
}}
.chip-importance {{
  letter-spacing: .06em;
  color: var(--brass);
  border-color: rgba(196, 163, 90, .35);
}}
.chip-importance:hover:not(:disabled):not(.is-disabled):not([aria-pressed="true"]) {{
  color: var(--brass);
  border-color: var(--brass);
}}
.chip-importance[aria-pressed="true"],
.chip-importance[aria-pressed="true"]:hover {{
  background: var(--brass);
  border-color: var(--brass);
  color: var(--bg);
}}
{color_css}
@media (prefers-reduced-motion: reduce) {{
  .classifier-chevron {{ transition: none; }}
}}
.home-footer {{
  display: flex; flex-wrap: wrap; align-items: center;
  justify-content: space-between; gap: .85rem;
  margin-top: .1rem; padding-top: 1rem;
  border-top: 1px solid var(--border);
}}
.home-count {{ font-weight: 600; font-size: .98rem; }}
.home-count span {{ color: var(--accent); font-family: var(--font-display); font-size: 1.2rem; }}
.home-hint {{ display: block; margin-top: .15rem; font-size: .8rem; color: var(--muted); }}
.demo-upsell {{
  margin: 0 0 1.1rem;
}}
.demo-upsell-link {{
  display: inline-block;
  padding: .55rem 1rem;
  border: 1px solid var(--accent);
  border-radius: var(--radius);
  color: var(--accent);
  font-size: .88rem;
  font-weight: 650;
  line-height: 1.35;
  text-decoration: none;
}}
.demo-upsell-link:hover {{
  background: var(--accent-soft);
  color: var(--accent-hover);
}}
.home-actions {{ display: flex; flex-wrap: wrap; gap: .55rem; align-items: center; }}
.btn-random {{
  appearance: none;
  border: 1px solid var(--border);
  background: var(--bg-elevated); color: var(--ink);
  border-radius: var(--radius); padding: .75rem 1.1rem;
  font: 650 .92rem var(--font-ui); cursor: pointer;
}}
.btn-random:hover:not(:disabled) {{ border-color: var(--accent); color: var(--accent); }}
.btn-random:disabled {{ opacity: .35; cursor: default; }}
.btn-start {{
  appearance: none; border: 0;
  background: var(--accent); color: var(--bg);
  border-radius: var(--radius); padding: .8rem 1.25rem;
  font: 650 .92rem var(--font-ui); cursor: pointer;
}}
.btn-start:disabled {{ opacity: .35; cursor: default; }}
.btn-start:not(:disabled):hover {{ background: var(--accent-hover); }}
.game-bar {{
  display: flex; flex-wrap: wrap; align-items: center;
  justify-content: space-between; gap: .75rem; margin-bottom: 1.15rem;
  position: relative;
  z-index: 60;
  overflow: visible;
}}
.btn-back {{
  appearance: none; border: 0; background: none; padding: 0;
  color: var(--accent); font: 600 .88rem var(--font-ui); cursor: pointer;
}}
.btn-back:hover {{ text-decoration: underline; text-underline-offset: 3px; }}
.game-summary {{
  font-size: .82rem; color: var(--muted); font-weight: 500;
  text-align: right; max-width: 28rem;
  line-height: 1.45;
  position: relative;
  overflow: visible;
}}
.game-summary-bit {{
  position: relative;
  display: inline-block;
  cursor: help;
  color: var(--ink);
  border-bottom: 1px dotted #9ca3af;
}}
.game-summary-bit.is-open .game-summary-tip,
.game-summary-bit:hover .game-summary-tip,
.game-summary-bit:focus-within .game-summary-tip {{
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}}
.game-summary-tip {{
  position: absolute;
  right: 0;
  top: calc(100% + .45rem);
  z-index: 70;
  min-width: 8rem;
  max-width: min(18rem, 70vw);
  padding: .55rem .7rem;
  background: var(--bg-elevated);
  color: var(--ink);
  border: 1px solid var(--border);
  border-radius: 4px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, .35);
  font-size: .78rem;
  font-weight: 500;
  line-height: 1.4;
  text-align: left;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-2px);
  transition: opacity .12s ease, visibility .12s ease, transform .12s ease;
  pointer-events: none;
}}
.game-summary-tip::before {{
  content: "";
  position: absolute;
  right: .85rem;
  top: -5px;
  width: 8px; height: 8px;
  background: var(--bg-elevated);
  border-left: 1px solid var(--border);
  border-top: 1px solid var(--border);
  transform: rotate(45deg);
}}
.game-summary-tip li {{
  margin: 0;
  padding: .1rem 0;
  list-style: none;
}}
.game-summary-tip ul {{
  margin: 0;
  padding: 0;
}}
.game-summary-sep {{ color: var(--muted); }}
.game-summary-static {{ color: var(--muted); }}
@media (max-width: 640px) {{
  .game-summary-tip {{ right: auto; left: 0; }}
  .game-summary-tip::before {{ right: auto; left: .85rem; }}
}}
.tags {{ display: flex; flex-wrap: wrap; gap: .28rem; margin-top: .4rem; }}
.tag {{
  font-size: .68rem; font-weight: 600;
  padding: .12rem .45rem; border-radius: 999px;
  background: var(--bg); color: var(--muted);
}}
.study {{ display: flex; flex-direction: column; align-items: center; gap: .85rem; overflow: visible; }}
.study-main {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: .75rem;
  width: 100%;
  max-width: 36rem;
  overflow: visible;
}}
.stage {{
  perspective: 1600px;
  width: 100%;
  overflow: visible;
}}
.study-details {{
  display: none;
  flex-direction: column;
  gap: .65rem;
  width: 100%;
  -webkit-user-select: none;
  user-select: none;
}}
.study-main.is-open .study-details {{ display: flex; }}
.study-under {{
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: .7rem;
}}
.detail-box {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: .75rem .85rem .85rem;
  -webkit-user-select: none;
  user-select: none;
}}
.detail-box h3 {{
  margin: 0 0 .45rem;
  font-size: .68rem;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--muted);
}}
.detail-box p {{
  margin: 0;
  font-size: .88rem;
  line-height: 1.45;
  color: var(--ink);
  white-space: pre-wrap;
  -webkit-user-select: none;
  user-select: none;
}}
.detail-box p.is-empty {{
  color: var(--muted);
  font-style: italic;
}}
.face,
.face .term,
.face .def,
.verso-title,
.face-stars {{
  -webkit-user-select: none;
  user-select: none;
}}
.terms,
.term-row {{
  -webkit-user-select: none;
  user-select: none;
}}
.btn-details {{
  appearance: none;
  border: 1px solid var(--border);
  background: var(--bg-elevated);
  color: var(--muted);
  border-radius: 999px;
  padding: .45rem .95rem;
  font: 600 .82rem var(--font-ui);
  cursor: pointer;
  transition: border-color .15s, color .15s, background .15s;
}}
.btn-details:hover {{ border-color: var(--accent); color: var(--accent); }}
.btn-details[aria-expanded="true"] {{
  background: var(--accent);
  border-color: var(--accent);
  color: var(--bg);
}}
.empty-filter {{
  display: none; text-align: center; color: var(--muted); width: 100%;
  padding: 2rem 1rem; border: 1px dashed var(--border); border-radius: var(--radius);
}}
.empty-filter.show {{ display: block; }}
.stage.is-hidden, .study-under.is-hidden, .progress.is-hidden, .btn-details.is-hidden {{ display: none; }}
.progress {{
  width: min(100%, 28rem); height: 2px; background: rgba(232, 235, 230, .1); overflow: hidden;
  border-radius: 99px;
}}
.progress > span {{
  display: block; height: 100%; width: 0%;
  background: var(--accent); transition: width .25s ease;
}}
.flip-scene {{
  width: 100%; height: auto; min-height: 18rem;
  cursor: pointer; border: 0; padding: 0; background: none;
  color: inherit; font: inherit; text-align: inherit; display: block;
}}
.flip-inner {{
  position: relative; width: 100%; height: auto; min-height: 18rem; display: grid;
  transform-style: preserve-3d;
  transition: transform .6s cubic-bezier(.2,.7,.15,1);
}}
.flip-scene.is-flipped .flip-inner {{ transform: rotateY(180deg); }}
.face {{
  grid-area: 1 / 1;
  backface-visibility: hidden; -webkit-backface-visibility: hidden;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  display: grid;
  place-items: center;
  padding: 1.75rem 2rem;
  overflow: visible;
  min-height: 18rem;
  box-sizing: border-box;
}}
.face-recto {{
  grid-template-rows: auto 1fr;
  align-items: stretch;
  justify-items: stretch;
}}
.face-stars {{
  justify-self: end;
  align-self: start;
  min-height: 1.1rem;
  font-size: .95rem;
  line-height: 1;
  letter-spacing: .08em;
  color: var(--brass);
}}
.face-recto .face-stars {{
  font-size: 1.35rem;
  min-height: 1.4rem;
  letter-spacing: .1em;
}}
.face-verso {{
  background: var(--card-verso);
  transform: rotateY(180deg);
  grid-template-rows: auto 1fr;
  align-items: stretch;
  justify-items: stretch;
  place-items: stretch stretch;
  position: relative;
}}
.face-verso-head {{
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: .65rem 1rem;
  align-items: start;
  width: 100%;
}}
.verso-title {{
  margin: 0;
  font-family: var(--font-ui);
  font-size: var(--flip-verso-title-size, .72rem);
  font-weight: 700;
  line-height: 1.3;
  color: var(--ink);
  text-align: left;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}}
.face-verso .face-stars {{
  font-size: .95rem;
  min-height: 1.1rem;
  justify-self: end;
}}
.face-body {{
  display: grid; place-items: center;
  width: 100%; height: 100%;
  overflow: visible;
}}
.face-verso .face-body {{
  place-items: center stretch;
  align-content: center;
}}
.term {{
  margin: 0;
  font-family: var(--font-ui);
  font-size: var(--flip-term-size, clamp(1.05rem, 2.3vw, 1.4rem));
  font-weight: 600; line-height: 1.35;
  text-align: center;
}}
.def {{
  margin: 0;
  font-family: var(--font-ui);
  font-size: var(--flip-def-size, clamp(.92rem, 1.7vw, 1.05rem));
  font-weight: 500; line-height: 1.55;
  color: var(--muted);
  text-align: left;
  width: 100%;
}}
.def.is-empty {{ color: var(--muted); font-style: italic; text-align: center; }}
.stage {{
  position: relative;
  overflow: visible;
}}
/* Bulle classique à droite de la carte */
.fiche-hover {{
  position: absolute;
  left: calc(100% + .75rem);
  top: 50%;
  transform: translateY(-50%) translateX(.35rem);
  z-index: 8;
  width: min(22rem, 42vw);
  max-height: min(24rem, 70vh);
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  display: flex;
  flex-direction: column;
  padding: .9rem 0 .9rem 1rem;
  overflow: hidden;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 4px;
  box-shadow:
    0 1px 2px rgba(0, 0, 0, .2),
    0 10px 28px rgba(0, 0, 0, .35);
  box-sizing: border-box;
  text-align: left;
  -webkit-user-select: none;
  user-select: none;
  -webkit-touch-callout: none;
  cursor: default;
  transition: opacity .15s ease, visibility .15s ease, transform .15s ease;
}}
.fiche-hover-scroll {{
  flex: 1;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding-right: .65rem;
  scrollbar-width: thin;
  scrollbar-color: rgba(196, 163, 90, .42) transparent;
  background:
    linear-gradient(var(--bg-elevated) 28%, rgba(22, 32, 40, 0)) center top,
    linear-gradient(rgba(22, 32, 40, 0), var(--bg-elevated) 72%) center bottom;
  background-size: 100% 1.35rem, 100% 1.35rem;
  background-repeat: no-repeat;
  background-attachment: local, local;
}}
.fiche-hover-scroll::-webkit-scrollbar {{
  width: 4px;
}}
.fiche-hover-scroll::-webkit-scrollbar-track {{
  background: transparent;
  margin: .15rem 0;
}}
.fiche-hover-scroll::-webkit-scrollbar-thumb {{
  background: rgba(196, 163, 90, .32);
  border-radius: var(--radius);
  border: 1px solid transparent;
  background-clip: padding-box;
}}
.fiche-hover-scroll::-webkit-scrollbar-thumb:hover {{
  background: rgba(196, 163, 90, .58);
  background-clip: padding-box;
}}
.fiche-hover-scroll::-webkit-scrollbar-thumb:active {{
  background: var(--accent);
  background-clip: padding-box;
}}
.fiche-hover::before {{
  content: "";
  position: absolute;
  right: 100%;
  top: 1.4rem;
  border: 8px solid transparent;
  border-right-color: var(--border);
}}
.fiche-hover::after {{
  content: "";
  position: absolute;
  right: 100%;
  top: 1.5rem;
  border: 7px solid transparent;
  border-right-color: var(--bg-elevated);
  margin-right: -1px;
}}
.stage.is-fiche-peek .fiche-hover.has-content {{
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
  transform: translateY(-50%) translateX(0);
}}
.fiche-line {{
  margin: 0;
  font-family: var(--font-ui);
  font-size: .8rem;
  font-weight: 500;
  line-height: 1.42;
  color: var(--ink);
  text-align: justify;
  -webkit-user-select: none;
  user-select: none;
}}
.fiche-label {{
  font-family: var(--font-display);
  font-size: .68rem;
  font-weight: 700;
  letter-spacing: .05em;
  text-transform: uppercase;
  color: var(--secondary);
}}
.fiche-text {{
  font-family: inherit;
  font-size: inherit;
  font-weight: inherit;
  line-height: inherit;
  color: inherit;
}}
.fiche-line.is-empty .fiche-text {{
  color: var(--muted);
  font-style: italic;
}}
.fiche-line + .fiche-line {{
  margin-top: .5rem;
  padding-top: .45rem;
  border-top: 1px solid rgba(196, 163, 90, .14);
}}
.flip-scene.is-flipped {{ cursor: help; }}
.stage.is-fiche-peek {{ cursor: default; }}
@media (max-width: 920px) {{
  .fiche-hover {{
    left: 50%;
    top: auto;
    bottom: calc(100% + .7rem);
    width: min(94%, 22rem);
    max-height: min(40vh, 16rem);
    transform: translateX(-50%) translateY(.3rem);
  }}
  .stage.is-fiche-peek .fiche-hover.has-content {{
    transform: translateX(-50%) translateY(0);
  }}
  .fiche-hover::before {{
    right: auto;
    left: 1.4rem;
    top: 100%;
    border: 8px solid transparent;
    border-top-color: var(--border);
  }}
  .fiche-hover::after {{
    right: auto;
    left: 1.5rem;
    top: 100%;
    border: 7px solid transparent;
    border-top-color: var(--bg-elevated);
    margin-right: 0;
    margin-top: -1px;
  }}
}}
@media (max-width: 720px) {{
  .fiche-hover {{ padding: .75rem 0 .75rem .85rem; }}
  .fiche-hover-scroll {{ padding-right: .5rem; }}
}}
.controls {{
  width: 100%;
  display: grid; grid-template-columns: 1fr auto 1fr;
  align-items: center; gap: .5rem;
}}
.controls-left, .controls-right {{ display: flex; gap: .1rem; align-items: center; }}
.controls-right {{ justify-content: flex-end; }}
.controls-center {{
  display: flex; align-items: center; gap: .5rem;
  font-variant-numeric: tabular-nums;
  font-family: var(--font-ui);
  font-weight: 650; font-size: 1rem;
}}
.nav-btn, .tool-btn {{
  appearance: none; border: 0; background: transparent;
  width: 2.25rem; height: 2.25rem; border-radius: var(--radius);
  color: var(--ink); cursor: pointer; display: grid; place-items: center;
}}
.nav-btn:hover, .tool-btn:hover {{ background: var(--accent-soft); }}
.nav-btn:disabled {{ opacity: .28; cursor: default; }}
.nav-btn.is-primary {{ color: var(--accent); }}
.tool-btn.active {{ color: var(--accent); background: var(--accent-soft); }}
.sr-only {{
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0,0,0,0); border: 0;
}}
.terms {{ margin-top: 2.75rem; width: 100%; }}
.terms-title {{
  margin: 0 0 .85rem;
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 650;
  color: var(--ink);
  letter-spacing: -0.01em;
}}
.term-row {{
  list-style: none; display: grid; grid-template-columns: 1fr 1.35fr; gap: 1rem;
  background: var(--card);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: var(--radius);
  padding: .9rem 1rem; margin-bottom: .5rem;
}}
.term-row[hidden] {{ display: none !important; }}
.term-recto {{ font-family: var(--font-display); font-weight: 650; font-size: 1rem; }}
.term-verso {{ color: var(--muted); line-height: 1.45; font-size: .9rem; }}
.study-copy {{
  margin: 1rem 0 0;
  font-size: .72rem;
  color: var(--muted);
  line-height: 1.45;
}}
@media (max-width: 720px) {{
  .term-row {{ grid-template-columns: 1fr; }}
  .controls {{ grid-template-columns: auto 1fr auto; }}
  .home-footer {{ flex-direction: column; align-items: stretch; }}
  .home-actions {{ width: 100%; }}
  .btn-start, .btn-random {{ flex: 1; }}
  .game-summary {{ text-align: left; }}
  .face {{ padding: 1.35rem 1.4rem; }}
}}
@media (prefers-reduced-motion: reduce) {{
  .flip-inner, .progress > span {{ transition: none; }}
}}
:fullscreen .wrap, :-webkit-full-screen .wrap {{
  max-width: 48rem;
}}
:fullscreen .wrap.is-study, :-webkit-full-screen .wrap.is-study {{
  max-width: 36rem;
}}
</style>
</head>
<body>
<div class="wrap" id="app">
  <section class="screen" id="screen-home" aria-label="Accueil">
    <h1 class="page-title">{_esc(title)}</h1>
    <p class="page-sub">Choisissez un thème et/ou des notions, puis lancez l’étude.<br>Laissez vide pour tout le set ({n} cartes).</p>
    {demo_upsell_html}
    <div class="home-card">
      <div class="classifier" data-group-panel="theme">
        <div class="classifier-row">
          <button type="button" class="classifier-toggle" aria-expanded="false" aria-controls="chips-theme">
            <svg class="classifier-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>
            <span class="classifier-title">1- Thèmes <span class="classifier-hint">(1 seul choix)</span></span>
          </button>
          <button type="button" class="classifier-clear" data-clear="theme">Effacer la sélection</button>
        </div>
        <div class="classifier-slide">
          <div class="classifier-slide-inner">
            <div class="classifier-body">
              <div class="chips" id="chips-theme" role="group" aria-label="Thèmes">{theme_chips}</div>
            </div>
          </div>
        </div>
      </div>
      <div class="classifier" data-group-panel="notion">
        <div class="classifier-row">
          <button type="button" class="classifier-toggle" aria-expanded="false" aria-controls="chips-notion">
            <svg class="classifier-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>
            <span class="classifier-title">2- Notions <span class="classifier-hint">(filtre par sélection multiple)</span></span>
          </button>
          <button type="button" class="classifier-clear" data-clear="notion">Effacer la sélection</button>
        </div>
        <div class="classifier-slide">
          <div class="classifier-slide-inner">
            <div class="classifier-body">
              <div class="chips" id="chips-notion" role="group" aria-label="Notions">{notion_chips}</div>
            </div>
          </div>
        </div>
      </div>
      <div class="classifier" data-group-panel="importance">
        <div class="classifier-row">
          <button type="button" class="classifier-toggle" aria-expanded="false" aria-controls="chips-importance">
            <svg class="classifier-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>
            <span class="classifier-title">3- Importance <span class="classifier-hint">(filtre par sélection multiple)</span></span>
          </button>
          <button type="button" class="classifier-clear" data-clear="importance">Effacer la sélection</button>
        </div>
        <div class="classifier-slide">
          <div class="classifier-slide-inner">
            <div class="classifier-body">
              <div class="chips" id="chips-importance" role="group" aria-label="Importance">{importance_chips}</div>
            </div>
          </div>
        </div>
      </div>
      <div class="home-footer">
        <div>
          <div class="home-count"><span id="home-count">{n}</span> carte(s)</div>
          <span class="home-hint" id="home-hint">Tout le set</span>
        </div>
        <div class="home-actions">
          <button type="button" class="btn-random" id="btn-random">10 au hasard…</button>
          <button type="button" class="btn-start" id="btn-start">Étudier</button>
        </div>
      </div>
    </div>
  </section>

  <section class="screen" id="screen-game" hidden aria-label="Étude">
    <div class="game-bar">
      <button type="button" class="btn-back" id="btn-back">← Accueil</button>
      <div class="game-summary" id="game-summary"></div>
    </div>
    <section class="study" aria-label="Mode flashcards">
      <div class="progress" id="progress-wrap" aria-hidden="true"><span id="progress"></span></div>
      <div class="empty-filter" id="empty-filter">Aucune carte pour ces filtres.</div>
      <div class="study-main" id="study-layout">
        <div class="stage" id="stage-wrap">
          <button type="button" class="flip-scene" id="card" aria-label="Retourner la carte">
            <div class="flip-inner">
              <div class="face face-recto">
                <div class="face-stars" id="recto-stars"></div>
                <div class="face-body"><p class="term" id="recto-text"></p></div>
              </div>
              <div class="face face-verso">
                <div class="face-verso-head">
                  <p class="verso-title" id="verso-title"></p>
                  <div class="face-stars" id="verso-stars"></div>
                </div>
                <div class="face-body"><p class="def" id="verso-text"></p></div>
              </div>
            </div>
          </button>
          <div class="fiche-hover" id="fiche-hover" aria-hidden="true">
            <div class="fiche-hover-scroll">
            <p class="fiche-line" id="fiche-faits"><span class="fiche-label">Faits.</span> <span class="fiche-text"></span></p>
            <p class="fiche-line" id="fiche-enjeu"><span class="fiche-label">Enjeu juridique.</span> <span class="fiche-text"></span></p>
            <p class="fiche-line" id="fiche-solution"><span class="fiche-label">Solution.</span> <span class="fiche-text"></span></p>
            <p class="fiche-line" id="fiche-perspective"><span class="fiche-label">Perspective.</span> <span class="fiche-text"></span></p>
            </div>
          </div>
        </div>
        <div class="study-under" id="controls-wrap">
          <div class="controls">
            <div class="controls-left">
              <button type="button" class="tool-btn" id="play" title="Lecture auto (recto 3 s · verso 7 s)" aria-pressed="false">
                <span class="sr-only">Lecture</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>
              </button>
              <button type="button" class="tool-btn" id="shuffle" title="Mélanger" aria-pressed="false">
                <span class="sr-only">Mélanger</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M16 3h5v5M4 20l16-16M21 16v5h-5M15 15l6 6M4 4l5 5"/></svg>
              </button>
            </div>
            <div class="controls-center">
              <button type="button" class="nav-btn" id="prev" aria-label="Carte précédente">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M15 18l-6-6 6-6"/></svg>
              </button>
              <span id="counter">0 / 0</span>
              <button type="button" class="nav-btn is-primary" id="next" aria-label="Carte suivante">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M9 18l6-6-6-6"/></svg>
              </button>
            </div>
            <div class="controls-right">
              <button type="button" class="tool-btn" id="fullscreen" title="Plein écran">
                <span class="sr-only">Plein écran</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5"/></svg>
              </button>
            </div>
          </div>
          <button type="button" class="btn-details" id="btn-details" aria-expanded="false" aria-controls="study-details">
            Objet · Portée · Considérant
          </button>
        </div>
        <aside class="study-details" id="study-details" aria-label="Fiche complémentaire">
          <div class="detail-box">
            <h3>Objet</h3>
            <p id="detail-objet" class="is-empty">—</p>
          </div>
          <div class="detail-box">
            <h3>Portée</h3>
            <p id="detail-portee" class="is-empty">—</p>
          </div>
          <div class="detail-box">
            <h3>Considérant de principe</h3>
            <p id="detail-considerant" class="is-empty">—</p>
          </div>
        </aside>
      </div>
    </section>
    <section class="terms" aria-label="3 cartes au hasard">
      <h2 class="terms-title" id="terms-title">3 au hasard…</h2>
      <ul style="margin:0;padding:0" id="terms-list">
{terms}
      </ul>
      <p class="study-copy">© Éditions Particulières · Tous droits réservés · Reproductions / exportations interdites</p>
    </section>
  </section>
</div>
<script>
const DATA = {cards_json};
const ASIDE_DATA = {aside_json};
const PLAY_RECTO_MS = 3000;
const PLAY_VERSO_MS = 7000;
const selected = {{ theme: new Set(), notion: new Set(), importance: new Set() }};
let order = [];
let studyPool = null;
let i = 0;
let flipped = false;
let playing = false;
let playTimer = null;
let shuffled = false;
let inGame = false;
let detailsOpen = false;

const home = document.getElementById("screen-home");
const game = document.getElementById("screen-game");
const homeCount = document.getElementById("home-count");
const homeHint = document.getElementById("home-hint");
const btnStart = document.getElementById("btn-start");
const btnRandom = document.getElementById("btn-random");
const btnBack = document.getElementById("btn-back");
const btnDetails = document.getElementById("btn-details");
const studyLayout = document.getElementById("study-layout");
const appWrap = document.getElementById("app");
const gameSummary = document.getElementById("game-summary");
const cardEl = document.getElementById("card");
const rectoEl = document.getElementById("recto-text");
const rectoStars = document.getElementById("recto-stars");
const versoTitle = document.getElementById("verso-title");
const versoStars = document.getElementById("verso-stars");
const versoEl = document.getElementById("verso-text");
const ficheHover = document.getElementById("fiche-hover");
const ficheFaits = document.getElementById("fiche-faits");
const ficheEnjeu = document.getElementById("fiche-enjeu");
const ficheSolution = document.getElementById("fiche-solution");
const fichePerspective = document.getElementById("fiche-perspective");
const detailObjet = document.getElementById("detail-objet");
const detailPortee = document.getElementById("detail-portee");
const detailConsiderant = document.getElementById("detail-considerant");
const counterEl = document.getElementById("counter");
const progressEl = document.getElementById("progress");
const progressWrap = document.getElementById("progress-wrap");
const stageWrap = document.getElementById("stage-wrap");
const controlsWrap = document.getElementById("controls-wrap");
const emptyFilter = document.getElementById("empty-filter");
const prevBtn = document.getElementById("prev");
const nextBtn = document.getElementById("next");
const playBtn = document.getElementById("play");
const shuffleBtn = document.getElementById("shuffle");
const fsBtn = document.getElementById("fullscreen");

function setDetail(el, value) {{
  const text = (value || "").trim();
  el.textContent = text || "— Non renseigné —";
  el.classList.toggle("is-empty", !text);
}}

function setFicheLine(row, value) {{
  const textEl = row && row.querySelector ? row.querySelector(".fiche-text") : null;
  if (!textEl) return false;
  const text = (value || "").trim();
  textEl.textContent = text || "—";
  row.classList.toggle("is-empty", !text);
  return !!text;
}}

function fillFiche(c) {{
  if (!ficheHover) return;
  if (!c) {{
    ficheHover.classList.remove("has-content");
    ficheHover.setAttribute("aria-hidden", "true");
    setFicheLine(ficheFaits, "");
    setFicheLine(ficheEnjeu, "");
    setFicheLine(ficheSolution, "");
    setFicheLine(fichePerspective, "");
    return;
  }}
  const a = setFicheLine(ficheFaits, c.faits);
  const b = setFicheLine(ficheEnjeu, c.enjeu);
  const d = setFicheLine(ficheSolution, c.solution);
  const e = setFicheLine(fichePerspective, c.perspective);
  const has = a || b || d || e;
  ficheHover.classList.toggle("has-content", has);
  ficheHover.setAttribute("aria-hidden", has ? "false" : "true");
}}

function setDetailsOpen(open) {{
  detailsOpen = !!open;
  studyLayout.classList.toggle("is-open", detailsOpen);
  btnDetails.setAttribute("aria-expanded", detailsOpen ? "true" : "false");
}}

function selectedList(group) {{
  return [...selected[group]];
}}

function matchesFilters(card) {{
  return matchesFiltersExcept(card, null);
}}

/** Lot cartes : thème ∩ (notions en OU) ∩ (★ en OU). */
function matchesFiltersExcept(card, exceptGroup) {{
  const themes = selectedList("theme");
  const notions = selectedList("notion");
  const levels = selectedList("importance").map(Number);
  if (themes.length && !(card.themes || []).some(t => themes.includes(t))) return false;
  if (exceptGroup !== "notion" && notions.length && !(card.notions || []).some(n => notions.includes(n))) return false;
  if (exceptGroup !== "importance" && levels.length && !levels.includes(Number(card.importance_level) || 0)) return false;
  return true;
}}

function filteredIndexes() {{
  return DATA.map((_, idx) => idx).filter(idx => matchesFilters(DATA[idx]));
}}

function selectionHint() {{
  const themes = selectedList("theme");
  const notions = selectedList("notion");
  const levels = selectedList("importance");
  if (!themes.length && !notions.length && !levels.length) return "Tout le set";
  const bits = [];
  if (themes.length) bits.push(themes.length + " thème(s)");
  if (notions.length) bits.push(notions.length + " notion(s)");
  if (levels.length) bits.push(levels.length + " importance(s)");
  return bits.join(" · ");
}}

function escHtml(s) {{
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}}

function selectionTooltipBits() {{
  const themes = selectedList("theme");
  const notions = selectedList("notion");
  const levels = selectedList("importance");
  const bits = [];
  if (themes.length) {{
    bits.push({{ label: themes.length + " thème(s)", items: themes }});
  }}
  if (notions.length) {{
    bits.push({{ label: notions.length + " notion(s)", items: notions }});
  }}
  if (levels.length) {{
    bits.push({{
      label: levels.length + " importance(s)",
      items: levels.map(n => "★".repeat(Number(n)) || String(n)),
    }});
  }}
  return bits;
}}

function renderGameSummary({{ random10 = false, n = 0, poolSize = 0 }} = {{}}) {{
  const bits = selectionTooltipBits();
  const chunks = [];
  if (random10) {{
    chunks.push(
      '<span class="game-summary-static">10 au hasard'
      + (poolSize < 10 ? " (" + n + ")" : "")
      + "</span>"
    );
  }}
  if (!bits.length && !random10) {{
    chunks.push('<span class="game-summary-static">Tout le set</span>');
  }}
  bits.forEach(bit => {{
    const items = bit.items.map(it => "<li>" + escHtml(it) + "</li>").join("");
    chunks.push(
      '<span class="game-summary-bit" tabindex="0">'
      + '<span class="game-summary-bit-label">' + escHtml(bit.label) + "</span>"
      + '<span class="game-summary-tip" role="tooltip"><ul>' + items + "</ul></span>"
      + "</span>"
    );
  }});
  chunks.push('<span class="game-summary-static">' + n + " carte(s)</span>");
  gameSummary.innerHTML = chunks.join('<span class="game-summary-sep"> · </span>');
  // Clic / focus : utile tactile ; hover CSS pour desktop
  gameSummary.querySelectorAll(".game-summary-bit").forEach(bit => {{
    bit.addEventListener("click", (e) => {{
      e.preventDefault();
      const open = bit.classList.contains("is-open");
      gameSummary.querySelectorAll(".game-summary-bit.is-open").forEach(b => b.classList.remove("is-open"));
      if (!open) bit.classList.add("is-open");
    }});
  }});
}}

function updateHomeCount() {{
  updateChipAvailability();
  const n = filteredIndexes().length;
  homeCount.textContent = String(n);
  homeHint.textContent = selectionHint();
  btnStart.disabled = n === 0;
  btnRandom.disabled = n === 0;
}}

function tagsPresentInData() {{
  const themes = new Set();
  const notions = new Set();
  const importance = new Set();
  for (const card of DATA) {{
    (card.themes || []).forEach(t => themes.add(t));
    (card.notions || []).forEach(n => notions.add(n));
    const lvl = Number(card.importance_level) || 0;
    if (lvl) importance.add(String(lvl));
  }}
  return {{ themes, notions, importance }};
}}

/**
 * Cascade unidirectionnelle 1→2→3 (capsules) :
 * 1 Thème borne notions + ★
 * 2 Notions refiltrent ★ uniquement (jamais l'inverse)
 * 3 Importance ne touche que le lot cartes, pas les capsules Notions
 */
function cardMatchesUpstream(card, opts) {{
  const themes = selectedList("theme");
  const notions = selectedList("notion");
  const levels = selectedList("importance").map(Number);
  const applyTheme = !opts || opts.applyTheme !== false;
  const applyNotion = !!(opts && opts.applyNotion);
  const applyImportance = !!(opts && opts.applyImportance);
  if (applyTheme && themes.length && !(card.themes || []).some(t => themes.includes(t))) return false;
  if (applyNotion && notions.length && !(card.notions || []).some(n => notions.includes(n))) return false;
  if (applyImportance && levels.length && !levels.includes(Number(card.importance_level) || 0)) return false;
  return true;
}}

function collectTags(pred) {{
  const themes = new Set();
  const notions = new Set();
  const importance = new Set();
  for (const card of DATA) {{
    if (!pred(card)) continue;
    (card.themes || []).forEach(t => themes.add(t));
    (card.notions || []).forEach(n => notions.add(n));
    const lvl = Number(card.importance_level) || 0;
    if (lvl) importance.add(String(lvl));
  }}
  return {{ themes, notions, importance }};
}}

function setChipState(btn, ok, exclusiveDim) {{
  btn.classList.toggle("is-disabled", !ok);
  btn.classList.toggle("is-exclusive-dim", !!exclusiveDim);
  btn.disabled = !ok;
  btn.setAttribute("aria-disabled", ok ? "false" : "true");
}}

function updateChipAvailability() {{
  const present = tagsPresentInData();
  const themeExclusive = selected.theme.size > 0;
  const hasLower = selected.notion.size > 0 || selected.importance.size > 0;

  // 2- Notions : uniquement le thème (Importance n'intervient jamais)
  let notionScope = collectTags(card =>
    cardMatchesUpstream(card, {{ applyTheme: true, applyNotion: false, applyImportance: false }})
  );
  // 3- ★ : thème + notions (pairs ★ cumulables)
  let starScope = collectTags(card =>
    cardMatchesUpstream(card, {{ applyTheme: true, applyNotion: true, applyImportance: false }})
  );
  // 1- Thèmes : catalogue, ou thèmes du lot Notion/★ si on a commencé par le bas
  let themeScope = hasLower
    ? collectTags(card =>
        cardMatchesUpstream(card, {{ applyTheme: false, applyNotion: true, applyImportance: true }})
      )
    : present;

  document.querySelectorAll('.chip[data-group="notion"]').forEach(btn => {{
    if (selected.notion.has(btn.dataset.value) && !notionScope.notions.has(btn.dataset.value)) {{
      selected.notion.delete(btn.dataset.value);
      btn.setAttribute("aria-pressed", "false");
    }}
  }});
  // Recalcul ★ après éventuel prune notions (changement de thème)
  starScope = collectTags(card =>
    cardMatchesUpstream(card, {{ applyTheme: true, applyNotion: true, applyImportance: false }})
  );
  document.querySelectorAll('.chip[data-group="importance"]').forEach(btn => {{
    if (selected.importance.has(btn.dataset.value) && !starScope.importance.has(btn.dataset.value)) {{
      selected.importance.delete(btn.dataset.value);
      btn.setAttribute("aria-pressed", "false");
    }}
  }});
  if (hasLower) {{
    themeScope = collectTags(card =>
      cardMatchesUpstream(card, {{ applyTheme: false, applyNotion: true, applyImportance: true }})
    );
  }}

  document.querySelectorAll(".chip").forEach(btn => {{
    const group = btn.dataset.group;
    const value = btn.dataset.value;
    const isSelected = selected[group].has(value);
    let ok = true;
    let exclusiveDim = false;

    if (group === "theme") {{
      ok = themeScope.themes.has(value);
      exclusiveDim = themeExclusive && !isSelected && ok;
    }} else if (group === "notion") {{
      ok = notionScope.notions.has(value);
    }} else if (group === "importance") {{
      ok = starScope.importance.has(value);
    }}

    setChipState(btn, ok, exclusiveDim);
  }});
}}

function shuffleArray(arr) {{
  const a = [...arr];
  for (let k = a.length - 1; k > 0; k--) {{
    const j = Math.floor(Math.random() * (k + 1));
    [a[k], a[j]] = [a[j], a[k]];
  }}
  return a;
}}

function syncTermsList(order) {{
  const list = document.getElementById("terms-list");
  if (!list) return;
  list.style.display = "flex";
  list.style.flexDirection = "column";
  const rows = Array.from(list.querySelectorAll(".term-row"));
  const byIdx = new Map(rows.map(el => [Number(el.dataset.idx), el]));
  const inOrder = new Set(order);
  const frag = document.createDocumentFragment();
  order.forEach((idx, pos) => {{
    const el = byIdx.get(idx);
    if (!el) return;
    el.hidden = false;
    el.style.order = String(pos);
    frag.appendChild(el);
  }});
  rows.forEach(el => {{
    const idx = Number(el.dataset.idx);
    if (inOrder.has(idx)) return;
    el.hidden = true;
    el.style.order = "999999";
    frag.appendChild(el);
  }});
  list.appendChild(frag);
}}

/** 3 cartes au hasard sous le flip.
 * Démo : tire dans ASIDE_DATA (pool hors lot d'étude).
 * Complet : hors du set d'étude, sauf si le set couvre presque tout. */
function pickAsideCards(count = 3) {{
  if (ASIDE_DATA && ASIDE_DATA.length) {{
    const pool = ASIDE_DATA.map((_, idx) => idx);
    return shuffleArray(pool).slice(0, Math.min(count, pool.length));
  }}
  const total = DATA.length;
  const studySet = new Set(
    (studyPool && studyPool.length) ? studyPool : (order || [])
  );
  // Filtre d'accueil (thème/notion/…) : priorité, sinon tout le catalogue
  const filtered = filteredIndexes();
  const base = filtered.length ? filtered : DATA.map((_, idx) => idx);
  // Exception : set d'étude trop large pour exclure (hors set < 3)
  const relax = studySet.size >= Math.max(0, total - 3);
  let pool;
  if (relax) {{
    pool = base.slice();
  }} else {{
    pool = base.filter(idx => !studySet.has(idx));
    if (pool.length < count) {{
      pool = DATA.map((_, idx) => idx).filter(idx => !studySet.has(idx));
    }}
    if (pool.length < count) {{
      const need = count - pool.length;
      const fromSet = shuffleArray(
        base.filter(idx => studySet.has(idx))
      ).slice(0, need);
      pool = pool.concat(fromSet);
    }}
  }}
  if (!pool.length) pool = base.slice();
  return shuffleArray(pool).slice(0, Math.min(count, pool.length));
}}

function refreshAsideList() {{
  const picks = pickAsideCards(3);
  syncTermsList(picks);
  const title = document.getElementById("terms-title");
  const section = title && title.closest(".terms");
  if (title) {{
    title.textContent = picks.length
      ? (picks.length === 3 ? "3 au hasard…" : picks.length + " au hasard…")
      : "3 au hasard…";
  }}
  if (section) section.hidden = picks.length === 0;
}}

function rebuildOrder() {{
  order = studyPool ? [...studyPool] : filteredIndexes();
  if (shuffled) order = shuffleArray(order);
  i = 0;
  flipped = false;
  refreshAsideList();
  const visible = order.length;
  const empty = visible === 0;
  emptyFilter.classList.toggle("show", empty);
  progressWrap.classList.toggle("is-hidden", empty);
  stageWrap.classList.toggle("is-hidden", empty);
  controlsWrap.classList.toggle("is-hidden", empty);
  btnDetails.classList.toggle("is-hidden", empty);
  if (empty) setDetailsOpen(false);
  render();
}}

function current() {{
  if (!order.length) return null;
  return DATA[order[i]];
}}

function starsLabel(level) {{
  const n = Math.max(0, Math.min(4, Number(level) || 0));
  return n ? "★".repeat(n) : "";
}}

function render() {{
  const c = current();
  if (!c) {{
    rectoEl.textContent = "";
    rectoStars.textContent = "";
    versoTitle.textContent = "";
    versoStars.textContent = "";
    versoEl.textContent = "";
    fillFiche(null);
    setDetail(detailObjet, "");
    setDetail(detailPortee, "");
    setDetail(detailConsiderant, "");
    counterEl.textContent = "0 / 0";
    progressEl.style.width = "0%";
    return;
  }}
  rectoEl.textContent = c.recto;
  rectoStars.textContent = starsLabel(c.importance_level);
  versoTitle.textContent = c.recto || "";
  versoStars.textContent = starsLabel(c.importance_level);
  versoEl.textContent = c.verso || "— Verso non renseigné —";
  versoEl.classList.toggle("is-empty", !c.verso);
  fillFiche(c);
  setDetail(detailObjet, c.objet);
  setDetail(detailPortee, c.portee);
  setDetail(detailConsiderant, c.considerant);
  counterEl.textContent = (i + 1) + " / " + order.length;
  progressEl.style.width = ((i + 1) / order.length * 100) + "%";
  cardEl.classList.toggle("is-flipped", flipped);
  updateFichePeek();
  prevBtn.disabled = order.length < 2;
  nextBtn.disabled = order.length < 2;
}}

function go(n) {{
  if (!order.length) return;
  i = (n + order.length) % order.length;
  flipped = false;
  render();
}}

function flip() {{
  if (!inGame || !order.length) return;
  flipped = !flipped;
  render();
  if (playing) schedulePlayStep();
}}

function shuffleOrder() {{
  shuffled = !shuffled;
  shuffleBtn.classList.toggle("active", shuffled);
  shuffleBtn.setAttribute("aria-pressed", shuffled ? "true" : "false");
  rebuildOrder();
}}

function stopPlay() {{
  playing = false;
  playBtn.classList.remove("active");
  playBtn.setAttribute("aria-pressed", "false");
  if (playTimer) {{ clearTimeout(playTimer); playTimer = null; }}
}}

function schedulePlayStep() {{
  if (!playing || !order.length) return;
  if (playTimer) {{ clearTimeout(playTimer); playTimer = null; }}
  const delay = flipped ? PLAY_VERSO_MS : PLAY_RECTO_MS;
  playTimer = setTimeout(() => {{
    if (!playing) return;
    if (!flipped) {{
      flipped = true;
      render();
      schedulePlayStep();
    }} else {{
      go(i + 1);
      schedulePlayStep();
    }}
  }}, delay);
}}

function togglePlay() {{
  if (playing) {{ stopPlay(); return; }}
  if (!order.length) return;
  playing = true;
  playBtn.classList.add("active");
  playBtn.setAttribute("aria-pressed", "true");
  schedulePlayStep();
}}

function toggleFullscreen() {{
  const root = document.documentElement;
  if (!document.fullscreenElement) {{
    (root.requestFullscreen || root.webkitRequestFullscreen)?.call(root);
  }} else {{
    (document.exitFullscreen || document.webkitExitFullscreen)?.call(document);
  }}
}}

function enterGame({{ random10 = false }} = {{}}) {{
  const idxs = filteredIndexes();
  if (!idxs.length) return;
  stopPlay();
  // Toujours un ordre aléatoire à l'entrée (cartes + liste du dessous)
  shuffled = true;
  shuffleBtn.classList.add("active");
  shuffleBtn.setAttribute("aria-pressed", "true");
  if (random10) {{
    studyPool = shuffleArray(idxs).slice(0, Math.min(10, idxs.length));
  }} else {{
    studyPool = shuffleArray(idxs);
  }}
  rebuildOrder();
  const n = order.length;
  renderGameSummary({{ random10, n, poolSize: idxs.length }});
  home.hidden = true;
  game.hidden = false;
  inGame = true;
  appWrap.classList.add("is-study");
  window.scrollTo({{ top: 0, behavior: "smooth" }});
}}

function leaveGame() {{
  stopPlay();
  inGame = false;
  studyPool = null;
  pointerOverStage = false;
  stageWrap.classList.remove("is-fiche-peek");
  setDetailsOpen(false);
  game.hidden = true;
  home.hidden = false;
  appWrap.classList.remove("is-study");
  updateHomeCount();
  window.scrollTo({{ top: 0, behavior: "smooth" }});
}}

document.querySelectorAll(".chip").forEach(btn => {{
  btn.addEventListener("click", () => {{
    if (btn.disabled || btn.classList.contains("is-disabled")) return;
    const group = btn.dataset.group;
    const value = btn.dataset.value;
    if (group === "theme") {{
      // Un seul thème à la fois
      if (selected.theme.has(value)) {{
        selected.theme.delete(value);
      }} else {{
        selected.theme.clear();
        selected.theme.add(value);
      }}
      document.querySelectorAll('.chip[data-group="theme"]').forEach(c => {{
        c.setAttribute("aria-pressed", selected.theme.has(c.dataset.value) ? "true" : "false");
      }});
    }} else if (selected[group].has(value)) {{
      selected[group].delete(value);
      btn.setAttribute("aria-pressed", "false");
    }} else {{
      selected[group].add(value);
      btn.setAttribute("aria-pressed", "true");
    }}
    updateHomeCount();
  }});
}});

document.querySelectorAll(".classifier-toggle").forEach(btn => {{
  btn.addEventListener("click", () => {{
    const panel = btn.closest(".classifier");
    const slide = panel.querySelector(".classifier-slide");
    const inner = panel.querySelector(".classifier-slide-inner");
    const open = !panel.classList.contains("is-open");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const SPEED = 420;
    const from = slide.getBoundingClientRect().height;
    const to = open ? inner.scrollHeight : 0;
    const dist = Math.abs(to - from);
    const duration = reduce ? 0 : Math.min(1100, Math.max(320, (dist / SPEED) * 1000));

    if (slide._anim) {{
      slide._anim.cancel();
      slide._anim = null;
    }}

    panel.classList.toggle("is-open", open);
    btn.setAttribute("aria-expanded", open ? "true" : "false");

    if (duration === 0) {{
      slide.style.height = open ? "auto" : "0px";
      return;
    }}

    slide.style.height = from + "px";
    void slide.offsetHeight;
    const anim = slide.animate(
      [{{ height: from + "px" }}, {{ height: to + "px" }}],
      {{ duration, easing: "cubic-bezier(.2,.75,.25,1)", fill: "forwards" }}
    );
    slide._anim = anim;
    anim.onfinish = () => {{
      slide.style.height = open ? "auto" : "0px";
      anim.cancel();
      slide._anim = null;
    }};
  }});
}});

document.querySelectorAll("[data-clear]").forEach(btn => {{
  btn.addEventListener("click", (e) => {{
    e.preventDefault();
    e.stopPropagation();
    const group = btn.dataset.clear;
    selected[group].clear();
    document.querySelectorAll('.chip[data-group="' + group + '"]').forEach(c => {{
      c.setAttribute("aria-pressed", "false");
    }});
    updateHomeCount();
  }});
}});

function blockCopyOn(el) {{
  if (!el) return;
  ["copy", "cut", "contextmenu", "selectstart", "dragstart"].forEach((ev) => {{
    el.addEventListener(ev, (e) => {{
      e.preventDefault();
      e.stopPropagation();
    }});
  }});
}}

if (ficheHover) {{
  blockCopyOn(ficheHover);
  // Clic sur la fiche : ne retourne pas la carte (lecture)
  ficheHover.addEventListener("click", (e) => {{
    e.preventDefault();
    e.stopPropagation();
  }});
  ficheHover.addEventListener("mousedown", (e) => e.stopPropagation());
}}
blockCopyOn(document.getElementById("study-details"));
blockCopyOn(document.getElementById("card"));
blockCopyOn(document.getElementById("terms-list"));

/* Survol fiche hors du rotateY (overlay sur .stage) */
let pointerOverStage = false;
function updateFichePeek() {{
  const ok = pointerOverStage
    && flipped
    && ficheHover
    && ficheHover.classList.contains("has-content");
  stageWrap.classList.toggle("is-fiche-peek", !!ok);
}}
stageWrap.addEventListener("pointerenter", (e) => {{
  if (e.pointerType && e.pointerType !== "mouse") return;
  pointerOverStage = true;
  updateFichePeek();
}});
stageWrap.addEventListener("pointerleave", () => {{
  pointerOverStage = false;
  updateFichePeek();
}});
stageWrap.addEventListener("pointermove", (e) => {{
  if (e.pointerType && e.pointerType !== "mouse") return;
  if (!pointerOverStage) pointerOverStage = true;
  updateFichePeek();
}});

btnStart.addEventListener("click", () => enterGame());
btnRandom.addEventListener("click", () => enterGame({{ random10: true }}));
btnBack.addEventListener("click", leaveGame);
btnDetails.addEventListener("click", () => setDetailsOpen(!detailsOpen));
cardEl.addEventListener("click", flip);
prevBtn.addEventListener("click", () => {{ stopPlay(); go(i - 1); }});
nextBtn.addEventListener("click", () => {{ stopPlay(); go(i + 1); }});
playBtn.addEventListener("click", togglePlay);
shuffleBtn.addEventListener("click", () => {{ stopPlay(); shuffleOrder(); }});
fsBtn.addEventListener("click", toggleFullscreen);

document.addEventListener("keydown", (e) => {{
  if (!inGame) return;
  if (e.key === "ArrowLeft") {{ stopPlay(); go(i - 1); }}
  else if (e.key === "ArrowRight") {{ stopPlay(); go(i + 1); }}
  else if (e.key === "Escape") {{ leaveGame(); }}
  else if (e.key === " " || e.key === "Enter") {{
    if (e.target === document.body || e.target === cardEl || e.target === document.documentElement) {{
      e.preventDefault();
      flip();
    }}
  }}
}});

const RECTO_TO_IDX = new Map(DATA.map((c, idx) => [c.recto, idx]));

function findCardIndex(query) {{
  if (!query) return -1;
  const q = decodeURIComponent(String(query)).trim();
  if (RECTO_TO_IDX.has(q)) return RECTO_TO_IDX.get(q);
  const lower = q.toLowerCase();
  for (const [recto, idx] of RECTO_TO_IDX) {{
    if (recto.toLowerCase() === lower) return idx;
  }}
  return -1;
}}

function enterGameWithCard(idx) {{
  if (idx < 0 || idx >= DATA.length) return;
  stopPlay();
  shuffled = false;
  shuffleBtn.classList.remove("active");
  shuffleBtn.setAttribute("aria-pressed", "false");
  studyPool = [idx];
  rebuildOrder();
  i = 0;
  flipped = false;
  renderGameSummary({{ random10: false, n: 1, poolSize: 1 }});
  home.hidden = true;
  game.hidden = false;
  inGame = true;
  appWrap.classList.add("is-study");
  render();
  window.scrollTo({{ top: 0, behavior: "smooth" }});
}}

function applyDeepLink() {{
  const params = new URLSearchParams(location.search);
  const card = params.get("card") || params.get("recto");
  if (!card) return;
  const idx = findCardIndex(card);
  if (idx >= 0) enterGameWithCard(idx);
}}

applyDeepLink();
updateHomeCount();
</script>
<script src="../auth.js?v=4"></script>
<script src="../site-nav.js?v=16"></script>
</body>
</html>
"""


def write_html(
    rows: list[dict[str, str]],
    out_path: Path,
    *,
    title: str = DEFAULT_PAGE_TITLE,
    colors: dict[str, dict[str, str]] | None = None,
    classifier_rows: list[dict[str, str]] | None = None,
    aside_rows: list[dict[str, str]] | None = None,
    demo_upsell: bool = False,
) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        build_html_document(
            rows,
            title=title,
            colors=colors,
            classifier_rows=classifier_rows,
            aside_rows=aside_rows,
            demo_upsell=demo_upsell,
        ),
        encoding="utf-8",
    )
    return out_path


class FlipcardGenerator:
    """Écrit HTML et/ou JSON à partir des lignes matrice."""

    def convert_many_html(
        self,
        rows: list[dict[str, str]],
        out_path: Path,
        *,
        title: str = DEFAULT_PAGE_TITLE,
        classifier_rows: list[dict[str, str]] | None = None,
        aside_rows: list[dict[str, str]] | None = None,
        demo_upsell: bool = False,
    ) -> Path:
        return write_html(
            rows,
            out_path,
            title=title,
            classifier_rows=classifier_rows,
            aside_rows=aside_rows,
            demo_upsell=demo_upsell,
        )

    def convert_many_json(self, rows: list[dict[str, str]], out_path: Path) -> Path:
        return write_json(rows, out_path)

    def convert_row_html(self, row: dict[str, str], out_path: Path) -> Path:
        title = _get(row, "Nom", "title") or "Flipcard"
        return write_html([row], out_path, title=title)

    def convert_row_json(self, row: dict[str, str], out_path: Path) -> Path:
        return write_json([row], out_path)
