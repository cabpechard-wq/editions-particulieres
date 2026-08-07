"""Charte graphique — dérivée de commerce/templates/site.css (thème Amphithéâtre).

Impression Word : fond blanc, texte sombre ; or et typographies du site conservés.
"""

from __future__ import annotations

from docx.shared import RGBColor

# Couleurs site → équivalents print
INK = RGBColor(0x1E, 0x24, 0x29)       # texte principal (inverse de --bg)
MUTED = RGBColor(0x8B, 0x96, 0x9E)     # --muted
ACCENT = RGBColor(0xC4, 0xA3, 0x5A)    # --accent (or)
SECONDARY = RGBColor(0xC5, 0x6A, 0x2D) # --secondary (orange)
BORDER = "D8DCD8"                       # --border sur fond clair
ACCENT_SOFT = "F3EDE0"                  # --accent-soft sur papier blanc
QUOTE_BG = "F7F3EA"

# Encadrés callout — Bleu, Accent 1, Plus foncé 25 % (thème Word du .dotx)
CALLOUT_BORDER_THEME = "accent1"
CALLOUT_BORDER_SHADE = "BF"  # 75 % → Darker 25 %
CALLOUT_BORDER_SZ = 24       # 3 pt (unités = 1/8 pt)
CALLOUT_BORDER_SPACE = 6     # gouttière barre → texte (pt)
CALLOUT_PARA_SPACE_AFTER_PT = 6  # espacement entre § (comme le corps)

# Encadré « Fiche de décision » — cadre 4 côtés, marges internes un peu plus larges
FICHE_BOX_CELL_MARGIN_DXA = 140  # ~2,5 mm (gouttière intérieure)

# Polices (Google Fonts du site ; repli système si absentes)
FONT_DISPLAY = "Cormorant Garamond"
FONT_DISPLAY_FALLBACK = "Times New Roman"
FONT_BODY = "DM Sans"
FONT_BODY_FALLBACK = "Calibri"

# Tailles (pt) — calées sur .legal-prose / .site-title
SIZE_H1 = 28   # titre page — .legal-prose h1 / .site-title
SIZE_H2 = 20   # Notion H1 — .legal-prose h2
SIZE_H3 = 16   # Notion H2 — .legal-prose h3
SIZE_H4 = 13   # Notion H3
SIZE_H5 = 11.5 # Notion H4
SIZE_H6 = 10   # rubriques jurisprudence
SIZE_BODY = 11 # .legal-prose p (~0.92rem)
SIZE_SUBTITLE = 9.5  # .site-crumb / kicker

LINE_BODY = 1.65
LINE_TIGHT = 1.25
