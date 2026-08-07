"""Référentiel de styles Word — Manuel V1.

Charte visuelle : extract/word/theme.py (dérivée de site.css).
Modèle : extract/templates/Editions_Particulieres.dotx
"""

from __future__ import annotations

from pathlib import Path

# Styles builtin Word — noms exacts à définir dans le .dotx
# Title : non utilisé
STYLE_TITLE = "Title"  # réservé, non appliqué à l'export

STYLE_SUBTITLE = "Subtitle"
STYLE_H1 = "Heading 1"  # titre de la page Notion
STYLE_H2 = "Heading 2"  # Notion heading_1
STYLE_H3 = "Heading 3"  # Notion heading_2
STYLE_H4 = "Heading 4"  # Notion heading_3
STYLE_H5 = "Heading 5"  # Notion heading_4
STYLE_H6 = "Heading 6"  # rubriques fiches jurisprudence
STYLE_NORMAL = "Normal"
STYLE_LIST_BULLET = "List Paragraph"
STYLE_LIST_NUMBER = "List Number"
STYLE_QUOTE = "Quote"
STYLE_CALLOUT = "Encadré"

# Pied de page « Ressources complémentaires » — relations affichées
FOOTER_RELATION_KEYS = frozenset({"jurisprudence", "index"})

# Mapping type de bloc Notion → style paragraphe Word
NOTION_BLOCK_STYLE: dict[str, str] = {
    "heading_1": STYLE_H2,
    "heading_2": STYLE_H3,
    "heading_3": STYLE_H4,
    "heading_4": STYLE_H5,
    "paragraph": STYLE_NORMAL,
    "bulleted_list_item": STYLE_LIST_BULLET,
    "numbered_list_item": STYLE_LIST_NUMBER,
    "to_do": STYLE_LIST_BULLET,
    "quote": STYLE_QUOTE,
    "callout": STYLE_NORMAL,
    "toggle": STYLE_NORMAL,
    "code": STYLE_NORMAL,
    "divider": STYLE_NORMAL,
}

# Propriétés longues rendues en Quote (citations / considérants de principe)
QUOTE_PROPERTY_KEYS = frozenset(
    {
        "considérant de principe",
        "considerant de principe",
    }
)


def notion_heading_style(level: int) -> str:
    """Notion heading_1..4 → Heading 2..5."""
    mapping = {1: STYLE_H2, 2: STYLE_H3, 3: STYLE_H4, 4: STYLE_H5}
    return mapping.get(level, STYLE_NORMAL)


def page_title_style() -> str:
    return STYLE_H1


def template_path() -> Path:
    return Path(__file__).resolve().parents[1] / "templates" / "Editions_Particulieres.dotx"
