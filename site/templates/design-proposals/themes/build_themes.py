"""Génère les CSS complets des lots charte (sobre / dynamique) depuis site.css."""

from __future__ import annotations

import re
from pathlib import Path

# …/site/templates/design-proposals/themes/build_themes.py → repo root = parents[4]
ROOT = Path(__file__).resolve().parents[4]
BASE_CSS = ROOT / "site" / "templates" / "site.css"
OUT_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Lot 1 — sobre / épuré (quasi silence)
# ---------------------------------------------------------------------------
LOT1 = {
    "site-salle-lecture.css": {
        "lot": "1 · sobre",
        "label": "Salle de lecture - Jour",
        "tagline": "Monochrome — accent gris argenté très léger sur « Droit » et les titres de section.",
        "fonts": (
            "https://fonts.googleapis.com/css2?"
            "family=EB+Garamond:ital,wght@0,500;0,600;1,500"
            "&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap"
        ),
        "font_ui": '"IBM Plex Sans", system-ui, sans-serif',
        "font_display": '"EB Garamond", "Times New Roman", serif',
        "root": {
            "--bg": "#fafafa",
            "--bg-elevated": "#ffffff",
            "--ink": "#1a1a1a",
            "--muted": "#6b6b6b",
            "--accent": "#1a1a1a",
            "--accent-hover": "#000000",
            "--accent-soft": "rgba(26, 26, 26, .05)",
            "--manuel-quote-border": "rgba(26, 26, 26, .35)",
            "--manuel-h3": "#1a1a1a",
            "--manuel-h4": "#3a3a3a",
            "--manuel-h5": "#5a5a5a",
            "--manuel-encadre-border": "#9a9a9a",
            "--secondary-soft": "rgba(168, 168, 176, .12)",
            "--secondary": "#a8a8b0",
            "--border": "rgba(26, 26, 26, .1)",
            "--card": "#ffffff",
            "--radius": "0",
        },
        "body_bg": """  background-color: var(--bg);
  background-image: none;""",
        "extra": """
/* —— Salle de lecture - Jour (lot 1 · sobre) —— */
.site-nav {
  background: rgba(255, 255, 255, .97);
  border-bottom: 1px solid var(--border);
  box-shadow: none;
  backdrop-filter: none;
}
.site-nav-kicker {
  color: var(--muted);
  letter-spacing: .2em;
  font-weight: 500;
}
.site-nav-product { font-weight: 600; letter-spacing: -.01em; }
.site-nav-links > a:hover,
.site-nav-links > a.is-active {
  color: var(--ink);
  text-decoration: underline;
  text-underline-offset: .28em;
  text-decoration-thickness: 1px;
}
.site-hero-kicker {
  color: var(--muted);
  letter-spacing: .18em;
  font-weight: 500;
}
.site-title { font-weight: 500; letter-spacing: -.02em; }
.site-title-hero em { font-style: italic; color: var(--secondary); }
.site-section-header h2 { color: var(--secondary); }
.manuel-content .legal-prose > h2 { color: var(--secondary); }
.home-rule {
  height: 1px;
  background: var(--border);
  opacity: 1;
}
.ex-item {
  background: transparent;
  border: 1px solid transparent;
  border-bottom: 1px solid var(--border);
  border-radius: 0;
  box-shadow: none;
  padding-left: 0;
  padding-right: 0;
}
.ex-item:hover {
  border-color: transparent;
  border-bottom-color: var(--ink);
  box-shadow: none;
  transform: none;
  background: transparent;
}
.ex-item-type {
  letter-spacing: .14em;
  color: var(--muted);
  font-weight: 500;
}
.ex-item-cta { color: var(--muted); font-weight: 500; }
.ex-item:hover .ex-item-cta { color: var(--ink); }
.home-access-card {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 0;
  box-shadow: none;
}
.home-access-card.is-accent {
  background: transparent;
  border-color: var(--ink);
}
.btn.fill-secondary {
  background: var(--ink);
  color: #fff;
  border-radius: 0;
}
.btn.outline-accent {
  border-color: var(--ink);
  color: var(--ink);
  border-radius: 0;
}
.btn { border-radius: 0; box-shadow: none; }
.btn-capsule {
  background: transparent;
  color: var(--ink) !important;
  border-color: var(--border);
}
.manuel-nav-side {
  border-right: 1px solid var(--border);
  background: transparent;
}
blockquote, .manuel-prose blockquote {
  border-color: var(--ink);
  background: transparent;
  border-width: 0 0 0 1px;
}
.encadre {
  border: 1px solid var(--border);
  background: transparent;
}
.site-footer {
  border-top: 1px solid var(--border);
  background: transparent;
}
.site-nav-user { border-radius: 0; }
""",
    },
    "site-salle-lecture-access-jour.css": {
        "lot": "1 · accessibilité",
        "label": "Salle de lecture (accessibilité) - Jour",
        "tagline": "Noir sur fond jaune — contraste optimal pour les yeux, texte agrandi, Atkinson Hyperlegible.",
        "fonts": (
            "https://fonts.googleapis.com/css2?"
            "family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400;1,700&display=swap"
        ),
        "font_ui": '"Atkinson Hyperlegible", system-ui, sans-serif',
        "font_display": '"Atkinson Hyperlegible", system-ui, sans-serif',
        "root": {
            "--bg": "#ffe03d",
            "--bg-elevated": "#ffe03d",
            "--ink": "#000000",
            "--muted": "#1a1a1a",
            "--accent": "#000000",
            "--accent-hover": "#000000",
            "--accent-soft": "rgba(0, 0, 0, .1)",
            "--manuel-quote-border": "#000000",
            "--manuel-h3": "#000000",
            "--manuel-h4": "#000000",
            "--manuel-h5": "#1a1a1a",
            "--manuel-encadre-border": "#000000",
            "--secondary-soft": "rgba(0, 0, 0, .08)",
            "--secondary": "#000000",
            "--border": "#000000",
            "--card": "#ffe03d",
            "--radius": "0",
        },
        "body_bg": """  background-color: var(--bg);
  background-image: none;""",
        "extra": """
/* —— Salle de lecture (accessibilité) - Jour (noir sur jaune) —— */
html { font-size: 125%; }
html, body {
  line-height: 1.65;
  letter-spacing: .01em;
  word-spacing: .04em;
  background: #ffe03d;
  color: #000;
}
.site-nav {
  background: #ffe03d;
  border-bottom: 3px solid #000;
  backdrop-filter: none;
  min-height: 4rem;
}
.site-nav-kicker {
  color: #000;
  letter-spacing: .12em;
  font-weight: 700;
  font-size: .75rem;
}
.site-nav-product {
  font-weight: 700;
  font-size: 1.25rem;
}
.site-nav-links {
  font-size: .95rem;
  font-weight: 700;
  gap: .5rem 1.1rem;
}
.site-nav-links > a {
  color: #000;
  padding: .45rem .35rem;
  text-decoration: underline;
  text-underline-offset: .22em;
  text-decoration-thickness: 2px;
}
.site-nav-links > a.is-active {
  background: #000;
  color: #ffe03d;
  text-decoration: none;
  padding: .45rem .7rem;
}
.site-nav-links > a:focus-visible,
.btn:focus-visible,
a:focus-visible {
  outline: 3px solid #000;
  outline-offset: 3px;
}
.site-hero-kicker {
  color: #000;
  font-weight: 700;
  letter-spacing: .12em;
  font-size: .8rem;
}
.site-title {
  font-weight: 700;
  letter-spacing: 0;
  line-height: 1.25;
}
.site-title-hero {
  font-size: clamp(2.2rem, 5.5vw, 3.4rem) !important;
  font-weight: 700;
}
.site-title-hero em {
  font-style: normal;
  font-weight: 700;
  color: #000;
  text-decoration: underline;
  text-decoration-thickness: 3px;
  text-underline-offset: .12em;
}
.site-lead,
.ex-item-desc,
.home-access-card p,
.manuel-prose,
.legal-prose {
  font-size: 1.1rem;
  line-height: 1.7;
  color: #000;
}
.home-rule {
  height: 3px;
  background: #000;
  opacity: 1;
}
.ex-item {
  background: #ffe03d;
  border: 2px solid #000;
  border-radius: 0;
  box-shadow: none;
  padding: 1.15rem 1.1rem;
}
.ex-item:hover {
  background: #000;
  color: #ffe03d;
  transform: none;
  box-shadow: none;
}
.ex-item:hover .ex-item-type,
.ex-item:hover .ex-item-title,
.ex-item:hover .ex-item-desc,
.ex-item:hover .ex-item-cta {
  color: #ffe03d;
}
.ex-item-type {
  color: #000;
  font-weight: 700;
  letter-spacing: .08em;
  font-size: .75rem;
}
.ex-item-title { font-weight: 700; font-size: 1.15rem; }
.ex-item-cta {
  color: #000;
  font-weight: 700;
  text-decoration: underline;
  text-decoration-thickness: 2px;
  text-underline-offset: .2em;
}
.home-access-card {
  background: #ffe03d;
  border: 3px solid #000;
  border-radius: 0;
  padding: 1.25rem;
}
.home-access-card.is-accent {
  background: #ffe03d;
  border-width: 4px;
}
.home-access-card h3 { font-weight: 700; font-size: 1.2rem; }
.btn {
  border-radius: 0;
  box-shadow: none;
  font-weight: 700;
  font-size: 1.05rem;
  min-height: 3rem;
  padding: .75rem 1.25rem;
  border-width: 2px;
}
.btn.fill-secondary {
  background: #000;
  color: #ffe03d;
  border: 2px solid #000;
}
.btn.outline-accent {
  border: 2px solid #000;
  color: #000;
  background: #ffe03d;
}
.manuel-nav-side {
  border-right: 3px solid #000;
  background: #ffe03d;
}
.manuel-nav-side a {
  font-weight: 700;
  color: #000;
  padding: .45rem 0;
}
.manuel-nav-side a.is-current {
  text-decoration: underline;
  text-decoration-thickness: 3px;
  text-underline-offset: .2em;
}
blockquote, .manuel-prose blockquote {
  border-color: #000;
  border-width: 0 0 0 4px;
  background: #ffd000;
  font-size: 1.1rem;
}
.encadre {
  border: 3px solid #000;
  background: #ffe03d;
  padding: 1rem 1.15rem;
}
.site-footer {
  border-top: 3px solid #000;
  background: #ffe03d;
}
.site-crumb, .site-footer-copy, .muted, .preview-label {
  color: #1a1a1a !important;
}
.site-nav-user { border-radius: 0; border: 2px solid #000; background: #ffe03d; }
""",
    },
    "site-salle-lecture-access-nuit.css": {
        "lot": "1 · accessibilité",
        "label": "Salle de lecture (accessibilité) - Nuit",
        "tagline": "Jaune sur noir — contraste optimal pour les yeux, texte agrandi, Atkinson Hyperlegible.",
        "fonts": (
            "https://fonts.googleapis.com/css2?"
            "family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400;1,700&display=swap"
        ),
        "font_ui": '"Atkinson Hyperlegible", system-ui, sans-serif',
        "font_display": '"Atkinson Hyperlegible", system-ui, sans-serif',
        "root": {
            "--bg": "#000000",
            "--bg-elevated": "#000000",
            "--ink": "#ffe03d",
            "--muted": "#e6c820",
            "--accent": "#ffe03d",
            "--accent-hover": "#fff176",
            "--accent-soft": "rgba(255, 224, 61, .12)",
            "--manuel-quote-border": "#ffe03d",
            "--manuel-h3": "#ffe03d",
            "--manuel-h4": "#ffe03d",
            "--manuel-h5": "#e6c820",
            "--manuel-encadre-border": "#ffe03d",
            "--secondary-soft": "rgba(255, 224, 61, .1)",
            "--secondary": "#ffe03d",
            "--border": "#ffe03d",
            "--card": "#000000",
            "--radius": "0",
        },
        "body_bg": """  background-color: var(--bg);
  background-image: none;""",
        "extra": """
/* —— Salle de lecture (accessibilité) - Nuit (jaune sur noir) —— */
html { font-size: 125%; }
html, body {
  line-height: 1.65;
  letter-spacing: .01em;
  word-spacing: .04em;
  color: #ffe03d;
  background: #000;
}
a { color: #ffe03d; }
a:hover { color: #fff176; }
.site-nav {
  background: #000;
  border-bottom: 3px solid #ffe03d;
  backdrop-filter: none;
  min-height: 4rem;
}
.site-nav-kicker {
  color: #ffe03d;
  letter-spacing: .12em;
  font-weight: 700;
  font-size: .75rem;
}
.site-nav-product {
  font-weight: 700;
  font-size: 1.25rem;
  color: #ffe03d;
}
.site-nav-links {
  font-size: .95rem;
  font-weight: 700;
  gap: .5rem 1.1rem;
}
.site-nav-links > a {
  color: #ffe03d;
  padding: .45rem .35rem;
  text-decoration: underline;
  text-underline-offset: .22em;
  text-decoration-thickness: 2px;
}
.site-nav-links > a.is-active {
  background: #ffe03d;
  color: #000;
  text-decoration: none;
  padding: .45rem .7rem;
}
.site-nav-links > a:focus-visible,
.btn:focus-visible,
a:focus-visible {
  outline: 3px solid #ffe03d;
  outline-offset: 3px;
}
.site-hero-kicker {
  color: #ffe03d;
  font-weight: 700;
  letter-spacing: .12em;
  font-size: .8rem;
}
.site-title {
  font-weight: 700;
  letter-spacing: 0;
  line-height: 1.25;
  color: #ffe03d;
}
.site-title-hero {
  font-size: clamp(2.2rem, 5.5vw, 3.4rem) !important;
  font-weight: 700;
  color: #ffe03d;
}
.site-title-hero em {
  font-style: normal;
  font-weight: 700;
  color: #ffe03d;
  text-decoration: underline;
  text-decoration-thickness: 3px;
  text-underline-offset: .12em;
}
.site-lead,
.ex-item-desc,
.home-access-card p,
.manuel-prose,
.legal-prose {
  font-size: 1.1rem;
  line-height: 1.7;
  color: #ffe03d;
}
.home-rule {
  height: 3px;
  background: #ffe03d;
  opacity: 1;
}
.ex-item {
  background: #000;
  border: 2px solid #ffe03d;
  border-radius: 0;
  box-shadow: none;
  padding: 1.15rem 1.1rem;
  color: #ffe03d;
}
.ex-item:hover {
  background: #ffe03d;
  color: #000;
  transform: none;
  box-shadow: none;
}
.ex-item:hover .ex-item-type,
.ex-item:hover .ex-item-title,
.ex-item:hover .ex-item-desc,
.ex-item:hover .ex-item-cta {
  color: #000;
}
.ex-item-type {
  color: #ffe03d;
  font-weight: 700;
  letter-spacing: .08em;
  font-size: .75rem;
}
.ex-item-title { font-weight: 700; font-size: 1.15rem; color: #ffe03d; }
.ex-item-cta {
  color: #ffe03d;
  font-weight: 700;
  text-decoration: underline;
  text-decoration-thickness: 2px;
  text-underline-offset: .2em;
}
.home-access-card {
  background: #000;
  border: 3px solid #ffe03d;
  border-radius: 0;
  padding: 1.25rem;
  color: #ffe03d;
}
.home-access-card.is-accent {
  background: #000;
  border-width: 4px;
  border-color: #ffe03d;
}
.home-access-card h3 { font-weight: 700; font-size: 1.2rem; color: #ffe03d; }
.btn {
  border-radius: 0;
  box-shadow: none;
  font-weight: 700;
  font-size: 1.05rem;
  min-height: 3rem;
  padding: .75rem 1.25rem;
  border-width: 2px;
}
.btn.fill-secondary {
  background: #ffe03d;
  color: #000;
  border: 2px solid #ffe03d;
}
.btn.outline-accent {
  border: 2px solid #ffe03d;
  color: #ffe03d;
  background: #000;
}
.manuel-nav-side {
  border-right: 3px solid #ffe03d;
  background: #000;
}
.manuel-nav-side a {
  font-weight: 700;
  color: #ffe03d;
  padding: .45rem 0;
}
.manuel-nav-side a.is-current {
  text-decoration: underline;
  text-decoration-thickness: 3px;
  text-underline-offset: .2em;
  color: #ffe03d;
}
blockquote, .manuel-prose blockquote {
  border-color: #ffe03d;
  border-width: 0 0 0 4px;
  background: #111;
  font-size: 1.1rem;
  color: #ffe03d;
}
.encadre {
  border: 3px solid #ffe03d;
  background: #000;
  padding: 1rem 1.15rem;
  color: #ffe03d;
}
.site-footer {
  border-top: 3px solid #ffe03d;
  background: #000;
  color: #ffe03d;
}
.site-footer-brand,
.site-footer a {
  color: #ffe03d;
}
.site-crumb, .site-footer-copy, .muted, .preview-label {
  color: #e6c820 !important;
}
.site-crumb a { color: #ffe03d; }
.site-nav-user {
  border-radius: 0;
  border: 2px solid #ffe03d;
  background: #000;
  color: #ffe03d;
}
""",
    },
    "site-salle-lecture-nuit.css": {
        "lot": "1 · accessibilité",
        "label": "Salle de lecture · Nuit",
        "tagline": "Blanc sur noir — accent laiton (filets Manuel) très léger sur « Droit » et les titres de section.",
        "fonts": (
            "https://fonts.googleapis.com/css2?"
            "family=EB+Garamond:ital,wght@0,500;0,600;1,500"
            "&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap"
        ),
        "font_ui": '"IBM Plex Sans", system-ui, sans-serif',
        "font_display": '"EB Garamond", "Times New Roman", serif',
        "root": {
            "--bg": "#000000",
            "--bg-elevated": "#0a0a0a",
            "--ink": "#ffffff",
            "--muted": "#b0b0b0",
            "--accent": "#ffffff",
            "--accent-hover": "#ffffff",
            "--accent-soft": "rgba(255, 255, 255, .08)",
            "--manuel-quote-border": "rgba(255, 255, 255, .45)",
            "--manuel-h3": "#ffffff",
            "--manuel-h4": "#e0e0e0",
            "--manuel-h5": "#b0b0b0",
            "--manuel-encadre-border": "#888888",
            "--secondary-soft": "rgba(196, 163, 90, .12)",
            "--secondary": "#c4a35a",
            "--border": "rgba(255, 255, 255, .22)",
            "--card": "#0a0a0a",
            "--radius": "0",
        },
        "body_bg": """  background-color: var(--bg);
  background-image: none;""",
        "extra": """
/* —— Salle de lecture · Nuit (blanc sur noir) —— */
.site-nav {
  background: rgba(0, 0, 0, .96);
  border-bottom: 1px solid var(--border);
  box-shadow: none;
  backdrop-filter: none;
}
.site-nav-kicker {
  color: var(--muted);
  letter-spacing: .2em;
  font-weight: 500;
}
.site-nav-product { font-weight: 600; letter-spacing: -.01em; color: #fff; }
.site-nav-links > a { color: var(--muted); }
.site-nav-links > a:hover,
.site-nav-links > a.is-active {
  color: #fff;
  text-decoration: underline;
  text-underline-offset: .28em;
  text-decoration-thickness: 1px;
}
.site-hero-kicker {
  color: var(--muted);
  letter-spacing: .18em;
  font-weight: 500;
}
.site-title { font-weight: 500; letter-spacing: -.02em; color: #fff; }
.site-title-hero em { font-style: italic; color: var(--secondary); }
.site-section-header h2 { color: var(--secondary); }
.manuel-content .legal-prose > h2 { color: var(--secondary); }
.home-rule {
  height: 1px;
  background: var(--border);
  opacity: 1;
}
.ex-item {
  background: transparent;
  border: 1px solid transparent;
  border-bottom: 1px solid var(--border);
  border-radius: 0;
  box-shadow: none;
  padding-left: 0;
  padding-right: 0;
}
.ex-item:hover {
  border-color: transparent;
  border-bottom-color: #fff;
  box-shadow: none;
  transform: none;
  background: transparent;
}
.ex-item-type {
  letter-spacing: .14em;
  color: var(--muted);
  font-weight: 500;
}
.ex-item-title { color: #fff; }
.ex-item-cta { color: var(--muted); font-weight: 500; }
.ex-item:hover .ex-item-cta { color: #fff; }
.home-access-card {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 0;
  box-shadow: none;
}
.home-access-card.is-accent {
  background: transparent;
  border-color: #fff;
}
.home-access-card h3 { color: #fff; }
.btn.fill-secondary {
  background: #fff;
  color: #000;
  border-radius: 0;
}
.btn.outline-accent {
  border-color: #fff;
  color: #fff;
  border-radius: 0;
}
.btn { border-radius: 0; box-shadow: none; }
.btn-capsule {
  background: transparent;
  color: #fff !important;
  border-color: var(--border);
}
.manuel-nav-side {
  border-right: 1px solid var(--border);
  background: transparent;
}
.manuel-nav-side a { color: var(--muted); }
.manuel-nav-side a.is-current,
.manuel-nav-side a:hover { color: #fff; }
blockquote, .manuel-prose blockquote {
  border-color: #fff;
  background: transparent;
  border-width: 0 0 0 1px;
}
.encadre {
  border: 1px solid var(--border);
  background: transparent;
}
.site-footer {
  border-top: 1px solid var(--border);
  background: transparent;
}
.site-nav-user {
  border-radius: 0;
  border-color: var(--border);
  background: #0a0a0a;
  color: #fff;
}
""",
    },
    "site-archives.css": {
        "lot": "1 · sobre",
        "label": "Archives",
        "tagline": "Gris froid, bleu-ardoise à peine perceptible — salle de lecture, catalogue, retenue.",
        "fonts": (
            "https://fonts.googleapis.com/css2?"
            "family=Source+Serif+4:ital,opsz,wght@0,8..60,500;0,8..60,600;1,8..60,500"
            "&family=Source+Sans+3:ital,wght@0,400;0,500;0,600;1,400&display=swap"
        ),
        "font_ui": '"Source Sans 3", system-ui, sans-serif',
        "font_display": '"Source Serif 4", Georgia, serif',
        "root": {
            "--bg": "#f2f3f5",
            "--bg-elevated": "#f8f9fa",
            "--ink": "#24282e",
            "--muted": "#6a727c",
            "--accent": "#3d4f63",
            "--accent-hover": "#2c3a4a",
            "--accent-soft": "rgba(61, 79, 99, .07)",
            "--manuel-quote-border": "rgba(61, 79, 99, .4)",
            "--manuel-h3": "#3d4f63",
            "--manuel-h4": "#4a5a6c",
            "--manuel-h5": "#6a727c",
            "--manuel-encadre-border": "#7a8a9a",
            "--secondary-soft": "rgba(61, 79, 99, .06)",
            "--secondary": "#4a5a6c",
            "--border": "rgba(36, 40, 46, .12)",
            "--card": "#f8f9fa",
            "--radius": "2px",
        },
        "body_bg": """  background-color: var(--bg);
  background-image:
    linear-gradient(180deg, rgba(248, 249, 250, .9) 0%, transparent 22%);""",
        "extra": """
/* —— Archives (lot 1 · sobre) —— */
.site-nav {
  background: rgba(248, 249, 250, .96);
  border-bottom: 1px solid var(--border);
  box-shadow: none;
}
.site-nav-kicker {
  color: var(--accent);
  letter-spacing: .16em;
  font-weight: 500;
  opacity: .85;
}
.site-nav-product { font-weight: 600; }
.site-nav-links > a.is-active {
  color: var(--accent);
  box-shadow: inset 0 -1px 0 var(--accent);
}
.site-hero-kicker { color: var(--accent); opacity: .8; letter-spacing: .15em; }
.site-title { font-weight: 600; letter-spacing: -.015em; }
.site-title-hero em { font-style: italic; color: var(--accent); }
.home-rule {
  height: 1px;
  background: linear-gradient(90deg, var(--accent), transparent 70%);
  opacity: .45;
}
.ex-item {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 2px;
  box-shadow: none;
}
.ex-item:hover {
  border-color: rgba(61, 79, 99, .28);
  box-shadow: none;
  transform: none;
  background: #fff;
}
.ex-item-type {
  letter-spacing: .12em;
  color: var(--accent);
  font-weight: 500;
  opacity: .75;
}
.home-access-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 2px;
}
.home-access-card.is-accent {
  background: #fff;
  border-color: rgba(61, 79, 99, .28);
}
.btn.fill-secondary {
  background: var(--accent);
  color: #f8f9fa;
}
.btn.outline-accent {
  border-color: var(--accent);
  color: var(--accent);
}
.manuel-nav-side {
  border-right: 1px solid var(--border);
  background: rgba(248, 249, 250, .7);
}
blockquote, .manuel-prose blockquote {
  border-color: var(--accent);
  background: rgba(61, 79, 99, .04);
  border-width: 0 0 0 2px;
}
.encadre {
  border: 1px solid var(--manuel-encadre-border);
  background: rgba(61, 79, 99, .03);
}
.site-footer {
  border-top: 1px solid var(--border);
  background: var(--bg-elevated);
}
""",
    },
    "site-pierre.css": {
        "lot": "1 · sobre",
        "label": "Pierre",
        "tagline": "Pierre claire, charcoal, filets architecturaux — atrium universitaire, espace et calme.",
        "fonts": (
            "https://fonts.googleapis.com/css2?"
            "family=Newsreader:ital,opsz,wght@0,6..72,500;0,6..72,600;1,6..72,500"
            "&family=Figtree:ital,wght@0,400;0,500;0,600;1,400&display=swap"
        ),
        "font_ui": '"Figtree", system-ui, sans-serif',
        "font_display": '"Newsreader", Georgia, serif',
        "root": {
            "--bg": "#eceae6",
            "--bg-elevated": "#f5f4f1",
            "--ink": "#2a2926",
            "--muted": "#6f6c66",
            "--accent": "#4a5248",
            "--accent-hover": "#353b34",
            "--accent-soft": "rgba(74, 82, 72, .08)",
            "--manuel-quote-border": "rgba(74, 82, 72, .45)",
            "--manuel-h3": "#4a5248",
            "--manuel-h4": "#5c6358",
            "--manuel-h5": "#6f6c66",
            "--manuel-encadre-border": "#8a877e",
            "--secondary-soft": "rgba(74, 82, 72, .07)",
            "--secondary": "#5c6358",
            "--border": "rgba(42, 41, 38, .12)",
            "--card": "#f5f4f1",
            "--radius": "0",
        },
        "body_bg": """  background-color: var(--bg);
  background-image:
    linear-gradient(90deg, rgba(42, 41, 38, .035) 0, rgba(42, 41, 38, .035) 1px, transparent 1px),
    linear-gradient(180deg, rgba(245, 244, 241, .85) 0%, transparent 30%);
  background-size: 4.5rem 100%, auto;
  background-position: 0 0, 0 0;""",
        "extra": """
/* —— Pierre (lot 1 · sobre) —— */
.site-nav {
  background: rgba(245, 244, 241, .94);
  border-bottom: 1px solid var(--border);
  box-shadow: none;
}
.site-nav-kicker {
  color: var(--accent);
  letter-spacing: .18em;
  font-weight: 500;
}
.site-nav-product { font-weight: 600; }
.site-nav-links > a.is-active {
  color: var(--ink);
  border-bottom: 1px solid var(--ink);
  border-radius: 0;
  padding-bottom: .15rem;
}
.site-hero-kicker { color: var(--accent); letter-spacing: .16em; }
.site-title { font-weight: 500; letter-spacing: -.02em; }
.site-title-hero { line-height: 1.05; }
.site-title-hero em { font-style: italic; color: var(--accent); }
.home-hero { gap: 3rem; }
.home-rule {
  height: 1px;
  background: var(--ink);
  opacity: .18;
}
.ex-item {
  background: transparent;
  border: none;
  border-top: 1px solid var(--border);
  border-radius: 0;
  box-shadow: none;
  padding-top: 1.15rem;
}
.ex-item:hover {
  border-top-color: var(--accent);
  box-shadow: none;
  transform: none;
  background: transparent;
}
.ex-item-type {
  letter-spacing: .14em;
  font-weight: 500;
  color: var(--accent);
}
.home-access-card {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 0;
  position: relative;
}
.home-access-card::before {
  content: "";
  position: absolute;
  top: 0; left: 0;
  width: 1.25rem;
  height: 1px;
  background: var(--accent);
}
.home-access-card.is-accent {
  background: var(--bg-elevated);
  border-color: rgba(74, 82, 72, .28);
}
.btn.fill-secondary {
  background: var(--accent);
  color: #f5f4f1;
  border-radius: 0;
}
.btn.outline-accent {
  border-color: var(--accent);
  color: var(--accent);
  border-radius: 0;
}
.btn { border-radius: 0; }
.manuel-nav-side {
  border-right: 1px solid var(--border);
  background: transparent;
}
.manuel-prose h3 { font-weight: 600; letter-spacing: -.01em; }
blockquote, .manuel-prose blockquote {
  border-color: var(--accent);
  background: transparent;
  border-width: 0 0 0 1px;
  padding-left: 1.25rem;
}
.encadre {
  border: 1px solid var(--border);
  border-left: 2px solid var(--accent);
  background: transparent;
}
.site-footer {
  border-top: 1px solid var(--border);
  background: transparent;
}
.site-section-header h2 { font-weight: 500; }
""",
    },
}

# ---------------------------------------------------------------------------
# Lot 2 — dynamique (la couleur comme moteur)
# ---------------------------------------------------------------------------
LOT2 = {
    "site-collectif.css": {
        "lot": "2 · dynamique",
        "label": "Collectif",
        "tagline": "Bleu nuit + orange association — énergie des conférences et des collectifs étudiants.",
        "fonts": (
            "https://fonts.googleapis.com/css2?"
            "family=Literata:ital,opsz,wght@0,7..72,500;0,7..72,600;1,7..72,500"
            "&family=Syne:wght@500;600;700;800&display=swap"
        ),
        "font_ui": '"Syne", system-ui, sans-serif',
        "font_display": '"Literata", Georgia, serif',
        "root": {
            "--bg": "#07111f",
            "--bg-elevated": "#0f1f38",
            "--ink": "#eef3fb",
            "--muted": "#8fa3be",
            "--accent": "#ff6b2c",
            "--accent-hover": "#ff854f",
            "--accent-soft": "rgba(255, 107, 44, .16)",
            "--manuel-quote-border": "rgba(255, 107, 44, .75)",
            "--manuel-h3": "#ffb347",
            "--manuel-h4": "#ff8c5a",
            "--manuel-h5": "#c9d4e8",
            "--manuel-encadre-border": "#38bdf8",
            "--secondary-soft": "rgba(56, 189, 248, .14)",
            "--secondary": "#38bdf8",
            "--launch-stamp": "#ff6b2c",
            "--launch-stamp-bg": "rgba(255, 107, 44, 0.12)",
            "--border": "rgba(238, 243, 251, .12)",
            "--card": "#0f1f38",
            "--radius": "6px",
        },
        "body_bg": """  background-color: var(--bg);
  background-image:
    radial-gradient(ellipse 90% 60% at 10% -5%, rgba(37, 99, 235, .35) 0%, transparent 55%),
    radial-gradient(ellipse 50% 40% at 100% 20%, rgba(255, 107, 44, .22) 0%, transparent 50%),
    linear-gradient(180deg, #0a1628 0%, #07111f 100%);
  background-attachment: fixed;""",
        "extra": """
/* —— Collectif (lot 2 · dynamique) —— */
.site-nav {
  background: rgba(7, 17, 31, .88);
  border-bottom: 2px solid rgba(255, 107, 44, .35);
}
.site-nav-kicker { color: var(--accent); letter-spacing: .18em; }
.site-nav-links > a.is-active {
  color: var(--accent);
  text-shadow: 0 0 20px rgba(255, 107, 44, .35);
}
.site-title { font-weight: 600; }
.site-title-hero em { color: var(--accent); font-style: normal; }
.site-hero-kicker { color: var(--accent); }
.home-rule {
  height: 3px;
  background: linear-gradient(90deg, #2563eb, var(--accent), transparent 80%);
  opacity: 1;
}
.ex-item {
  border: 1px solid var(--border);
  background: linear-gradient(160deg, rgba(15, 31, 56, .95), rgba(7, 17, 31, .6));
  transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
}
.ex-item:hover {
  transform: translateY(-3px);
  border-color: rgba(255, 107, 44, .55);
  box-shadow: 0 14px 40px rgba(255, 107, 44, .12);
}
.ex-item-type { color: #38bdf8; }
.ex-item-cta { font-weight: 700; letter-spacing: .02em; color: var(--accent); }
.home-access-card.is-accent {
  border-color: rgba(255, 107, 44, .5);
  background: linear-gradient(135deg, rgba(255, 107, 44, .12), rgba(37, 99, 235, .08));
}
.btn.fill-secondary {
  background: var(--accent);
  color: #07111f;
  font-weight: 700;
}
.btn.outline-accent {
  border-color: var(--accent);
  color: var(--accent);
}
.btn { transition: transform .15s ease, box-shadow .15s ease; }
.btn:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(255, 107, 44, .2); }
.manuel-nav-side a:hover { color: var(--accent); padding-left: .35rem; transition: padding .15s ease; }
blockquote, .manuel-prose blockquote {
  border-color: var(--accent);
  background: rgba(255, 107, 44, .08);
}
.encadre {
  border-color: var(--manuel-encadre-border);
  background: rgba(56, 189, 248, .06);
}
.site-footer { border-top: 2px solid rgba(255, 107, 44, .25); }
@keyframes collectif-pulse {
  0%, 100% { opacity: .85; }
  50% { opacity: 1; }
}
.site-hero-kicker { animation: collectif-pulse 4s ease-in-out infinite; }
""",
    },
    "site-salle-td.css": {
        "lot": "2 · dynamique",
        "label": "Salle de TD",
        "tagline": "Bleu institution dominant + rouge parlementaire en accent — prise de parole, débat, clarté.",
        "fonts": (
            "https://fonts.googleapis.com/css2?"
            "family=Libre+Baskerville:ital,wght@0,400;0,700;1,400"
            "&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,700;1,9..40,400&display=swap"
        ),
        "font_ui": '"DM Sans", system-ui, sans-serif',
        "font_display": '"Libre Baskerville", Georgia, serif',
        "root": {
            "--bg": "#f7f5f2",
            "--bg-elevated": "#ffffff",
            "--ink": "#1a2332",
            "--muted": "#5c6575",
            "--accent": "#1e3a5f",
            "--accent-hover": "#152a45",
            "--accent-soft": "rgba(30, 58, 95, .1)",
            "--manuel-quote-border": "rgba(30, 58, 95, .65)",
            "--manuel-h3": "#1e3a5f",
            "--manuel-h4": "#c8102e",
            "--manuel-h5": "#5c6575",
            "--manuel-encadre-border": "#c8102e",
            "--secondary-soft": "rgba(200, 16, 46, .1)",
            "--secondary": "#c8102e",
            "--launch-stamp": "#c8102e",
            "--launch-stamp-bg": "rgba(200, 16, 46, 0.08)",
            "--border": "rgba(26, 35, 50, .12)",
            "--card": "#ffffff",
            "--radius": "4px",
        },
        "body_bg": """  background-color: var(--bg);
  background-image:
    linear-gradient(180deg, #ffffff 0%, transparent 18%),
    radial-gradient(ellipse 70% 45% at 100% 0%, rgba(30, 58, 95, .1) 0%, transparent 55%),
    radial-gradient(ellipse 50% 40% at 0% 100%, rgba(200, 16, 46, .06) 0%, transparent 50%);""",
        "extra": """
/* —— Salle de TD (lot 2 · dynamique) —— */
.site-nav {
  background: rgba(255, 255, 255, .95);
  border-bottom: 3px solid var(--accent);
  box-shadow: 0 1px 0 rgba(30, 58, 95, .06);
}
.site-nav-kicker {
  color: var(--accent);
  letter-spacing: .16em;
  font-weight: 700;
}
.site-nav-links > a.is-active {
  color: var(--accent);
  background: rgba(30, 58, 95, .08);
  padding: .35rem .55rem;
  border-radius: 4px;
}
.site-hero-kicker { color: var(--accent); font-weight: 700; }
.site-title { font-weight: 700; }
.site-title-hero { color: var(--accent); }
.site-title-hero em { color: var(--secondary); font-style: italic; }
.home-rule {
  height: 4px;
  background: linear-gradient(90deg, var(--accent) 0%, var(--accent) 28%, #c8102e 28%, #c8102e 55%, transparent 100%);
  opacity: 1;
}
.ex-item {
  background: var(--card);
  border: 1px solid var(--border);
  border-left: 3px solid transparent;
  transition: border-color .15s ease, box-shadow .15s ease, transform .15s ease;
}
.ex-item:hover {
  border-left-color: var(--accent);
  box-shadow: 0 10px 28px rgba(30, 58, 95, .1);
  transform: translateX(2px);
}
.ex-item-type { color: #c8102e; font-weight: 700; letter-spacing: .1em; }
.ex-item-cta { color: var(--accent); font-weight: 700; }
.home-access-card {
  border: 1px solid var(--border);
  background: #fff;
}
.home-access-card.is-accent {
  border-color: rgba(30, 58, 95, .35);
  background: linear-gradient(160deg, rgba(30, 58, 95, .07), #fff 55%);
}
.btn.fill-secondary {
  background: var(--accent);
  color: #fff;
  font-weight: 700;
}
.btn.outline-accent {
  border-color: #c8102e;
  color: #c8102e;
}
.btn.outline-accent:hover {
  background: #c8102e;
  color: #fff;
}
.manuel-nav-side {
  border-right: 1px solid var(--border);
  background: rgba(30, 58, 95, .03);
}
.manuel-nav-side a.is-current {
  color: var(--accent);
  font-weight: 700;
  border-left: 3px solid var(--accent);
  padding-left: .65rem;
}
blockquote, .manuel-prose blockquote {
  border-color: var(--accent);
  background: rgba(30, 58, 95, .05);
  border-width: 0 0 0 4px;
}
.encadre {
  border: 1px solid rgba(200, 16, 46, .25);
  border-left: 3px solid #c8102e;
  background: rgba(200, 16, 46, .04);
}
.site-footer {
  border-top: 3px solid var(--accent);
  background: #fff;
}
""",
    },
    "site-phare.css": {
        "lot": "2 · dynamique",
        "label": "Phare",
        "tagline": "Cobalt électrique + ambre signal — orientation claire, contrastes nets, rythme vif.",
        "fonts": (
            "https://fonts.googleapis.com/css2?"
            "family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,700;1,9..144,500"
            "&family=Outfit:wght@400;500;600;700&display=swap"
        ),
        "font_ui": '"Outfit", system-ui, sans-serif',
        "font_display": '"Fraunces", Georgia, serif',
        "root": {
            "--bg": "#f0f4fa",
            "--bg-elevated": "#ffffff",
            "--ink": "#0f172a",
            "--muted": "#64748b",
            "--accent": "#1d4ed8",
            "--accent-hover": "#1e40af",
            "--accent-soft": "rgba(29, 78, 216, .1)",
            "--manuel-quote-border": "rgba(29, 78, 216, .7)",
            "--manuel-h3": "#1d4ed8",
            "--manuel-h4": "#ca8a04",
            "--manuel-h5": "#64748b",
            "--manuel-encadre-border": "#eab308",
            "--secondary-soft": "rgba(234, 179, 8, .14)",
            "--secondary": "#ca8a04",
            "--launch-stamp": "#eab308",
            "--launch-stamp-bg": "rgba(234, 179, 8, 0.12)",
            "--border": "rgba(15, 23, 42, .1)",
            "--card": "#ffffff",
            "--radius": "8px",
        },
        "body_bg": """  background-color: var(--bg);
  background-image:
    radial-gradient(ellipse 80% 50% at 0% -10%, rgba(29, 78, 216, .14) 0%, transparent 50%),
    radial-gradient(ellipse 60% 40% at 100% 0%, rgba(234, 179, 8, .12) 0%, transparent 45%),
    linear-gradient(180deg, #e8eef8 0%, #f0f4fa 40%, #f0f4fa 100%);""",
        "extra": """
/* —— Phare (lot 2 · dynamique) —— */
.site-nav {
  background: rgba(255, 255, 255, .92);
  border-bottom: 1px solid var(--border);
  box-shadow: 0 4px 24px rgba(29, 78, 216, .06);
}
.site-nav-kicker {
  color: var(--accent);
  letter-spacing: .14em;
  font-weight: 700;
}
.site-nav-links > a.is-active {
  color: #fff;
  background: var(--accent);
  padding: .35rem .7rem;
  border-radius: 999px;
}
.site-hero-kicker { color: var(--accent); font-weight: 600; }
.site-title { font-weight: 700; font-variation-settings: "SOFT" 40; }
.site-title-hero em {
  color: var(--accent);
  font-style: italic;
  background: linear-gradient(120deg, rgba(29, 78, 216, .12), rgba(234, 179, 8, .15));
  padding: 0 .12em;
  border-radius: 4px;
}
.home-rule {
  height: 5px;
  border-radius: 3px;
  background: linear-gradient(90deg, var(--accent), #3b82f6 40%, #eab308 70%, transparent);
  opacity: 1;
}
.ex-item {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 2px 0 rgba(29, 78, 216, .04);
  transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
}
.ex-item:hover {
  transform: translateY(-4px);
  border-color: rgba(29, 78, 216, .35);
  box-shadow: 0 16px 36px rgba(29, 78, 216, .12);
}
.ex-item-type {
  color: #ca8a04;
  font-weight: 700;
  letter-spacing: .12em;
}
.ex-item-cta { color: var(--accent); font-weight: 700; }
.home-access-card {
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #fff;
}
.home-access-card.is-accent {
  border-color: transparent;
  background:
    linear-gradient(#fff, #fff) padding-box,
    linear-gradient(135deg, var(--accent), #eab308) border-box;
  border: 2px solid transparent;
}
.btn.fill-secondary {
  background: var(--accent);
  color: #fff;
  font-weight: 700;
  border-radius: 999px;
}
.btn.outline-accent {
  border-color: #ca8a04;
  color: #92400e;
  background: rgba(234, 179, 8, .12);
  border-radius: 999px;
  font-weight: 700;
}
.btn.outline-accent:hover {
  background: #eab308;
  color: #0f172a;
  border-color: #eab308;
}
.manuel-nav-side {
  border-right: 1px solid var(--border);
  background: rgba(29, 78, 216, .03);
}
blockquote, .manuel-prose blockquote {
  border-color: var(--accent);
  background: linear-gradient(90deg, rgba(29, 78, 216, .06), rgba(234, 179, 8, .05));
  border-width: 0 0 0 4px;
}
.encadre {
  border: 1px solid rgba(234, 179, 8, .45);
  background: rgba(234, 179, 8, .08);
  border-radius: 8px;
}
.site-footer {
  border-top: 1px solid var(--border);
  background: #fff;
  box-shadow: 0 -8px 32px rgba(29, 78, 216, .04);
}
""",
    },
}

# ---------------------------------------------------------------------------
# Lot 3 — carte blanche (créativité max : formes, textures, illustrations)
# ---------------------------------------------------------------------------
LOT3 = {
    "site-laboratoire.css": {
        "lot": "3 · carte blanche",
        "label": "Laboratoire",
        "tagline": "Teal + corail, formes découpées, grille de labo — esprit recherche et expérimentation.",
        "fonts": (
            "https://fonts.googleapis.com/css2?"
            "family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,700;1,9..144,500"
            "&family=Space+Grotesk:wght@400;500;600;700&display=swap"
        ),
        "font_ui": '"Space Grotesk", system-ui, sans-serif',
        "font_display": '"Fraunces", Georgia, serif',
        "root": {
            "--bg": "#f7f4ef",
            "--bg-elevated": "#ffffff",
            "--ink": "#1a1a1f",
            "--muted": "#64616a",
            "--accent": "#0d9488",
            "--accent-hover": "#0f766e",
            "--accent-soft": "rgba(13, 148, 136, .12)",
            "--manuel-quote-border": "rgba(244, 63, 94, .7)",
            "--manuel-h3": "#0d9488",
            "--manuel-h4": "#e11d48",
            "--manuel-h5": "#7c6f64",
            "--manuel-encadre-border": "#f43f5e",
            "--secondary-soft": "rgba(244, 63, 94, .1)",
            "--secondary": "#f43f5e",
            "--launch-stamp": "#f43f5e",
            "--launch-stamp-bg": "rgba(244, 63, 94, 0.1)",
            "--border": "rgba(26, 26, 31, .1)",
            "--card": "#ffffff",
            "--radius": "0",
        },
        "body_bg": """  background-color: var(--bg);
  background-image:
    url("./media/lab-grid.svg"),
    radial-gradient(circle at 0% 0%, rgba(13, 148, 136, .1) 0%, transparent 42%),
    radial-gradient(circle at 100% 100%, rgba(244, 63, 94, .08) 0%, transparent 38%);
  background-size: 120px 120px, auto, auto;
  background-attachment: fixed, scroll, scroll;""",
        "extra": """
/* —— Laboratoire (lot 3 · carte blanche) —— */
.site-nav {
  background: var(--bg-elevated);
  border-bottom: 3px solid var(--ink);
  border-image: linear-gradient(90deg, var(--accent) 0%, var(--accent) 32%, #f43f5e 32%, #f43f5e 68%, var(--ink) 68%) 1;
}
.site-nav-kicker {
  font-family: var(--font-ui);
  color: #f43f5e;
  letter-spacing: .2em;
}
.site-title { font-weight: 700; font-variation-settings: "SOFT" 50; }
.site-main { position: relative; }
.site-main::before {
  content: "";
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, var(--accent), #f43f5e);
  opacity: .85;
  pointer-events: none;
}
.home-amphitheatre .home-hero {
  display: grid;
  gap: 2.5rem;
}
.home-amphitheatre .home-hero-copy {
  position: relative;
  padding-right: clamp(0px, 8vw, 4rem);
}
.home-amphitheatre .home-hero-copy::after {
  content: "";
  display: block;
  margin-top: 1.5rem;
  width: min(100%, 22rem);
  aspect-ratio: 16 / 10;
  background: url("./media/lab-hero.svg") center / cover no-repeat;
  border: 2px solid var(--ink);
  clip-path: polygon(0 0, 100% 0, 100% calc(100% - 16px), calc(100% - 16px) 100%, 0 100%);
}
.home-rule {
  height: 6px;
  background: repeating-linear-gradient(
    90deg,
    var(--accent) 0 12px,
    transparent 12px 18px,
    #f43f5e 18px 24px,
    transparent 24px 30px
  );
  opacity: 1;
}
.ex-item {
  border: 2px solid var(--ink);
  border-radius: 0;
  background: var(--card);
  clip-path: polygon(0 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%);
}
.ex-item:hover {
  border-color: var(--accent);
  box-shadow: 8px 8px 0 rgba(26, 26, 31, .12);
  transform: translate(-2px, -2px);
}
.ex-item-type {
  font-family: var(--font-ui);
  text-transform: uppercase;
  letter-spacing: .14em;
  font-size: .62rem;
  color: #f43f5e;
}
.home-access-card {
  border: 2px solid var(--ink);
  border-radius: 0;
}
.home-access-card.is-accent {
  background: linear-gradient(135deg, rgba(13, 148, 136, .08), rgba(244, 63, 94, .06));
}
.btn.fill-secondary {
  background: var(--accent);
  color: #fff;
  border-radius: 0;
  font-weight: 700;
}
.btn.outline-accent {
  border: 2px solid #f43f5e;
  color: #f43f5e;
  border-radius: 0;
  font-weight: 700;
}
.manuel-prose h3::before {
  content: "§ ";
  color: #f43f5e;
  font-weight: 700;
}
blockquote, .manuel-prose blockquote {
  border-width: 0 0 0 4px;
  border-style: solid;
  border-color: #f43f5e;
  background: rgba(244, 63, 94, .05);
}
.encadre {
  border: 2px dashed var(--manuel-encadre-border);
  background: rgba(13, 148, 136, .04);
}
.site-footer {
  border-top: 3px solid var(--ink);
  background: var(--bg-elevated);
}
@keyframes lab-spin {
  to { transform: rotate(360deg); }
}
.site-hero-kicker::after {
  content: "";
  display: inline-block;
  width: .55rem; height: .55rem;
  margin-left: .45rem;
  border: 1.5px solid var(--accent);
  border-radius: 50%;
  vertical-align: middle;
  animation: lab-spin 8s linear infinite;
}
""",
    },
    "site-palimpseste.css": {
        "lot": "3 · carte blanche",
        "label": "Palimpseste",
        "tagline": "Couches d’écriture, indigo et vermillon — manuscrit vivant, annotations croisées.",
        "fonts": (
            "https://fonts.googleapis.com/css2?"
            "family=Cormorant+Infant:ital,wght@0,500;0,600;0,700;1,500;1,600"
            "&family=Schibsted+Grotesk:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap"
        ),
        "font_ui": '"Schibsted Grotesk", system-ui, sans-serif',
        "font_display": '"Cormorant Infant", "Times New Roman", serif',
        "root": {
            "--bg": "#e4dfd4",
            "--bg-elevated": "#efeae0",
            "--ink": "#1e1b4b",
            "--muted": "#5c5870",
            "--accent": "#dc2626",
            "--accent-hover": "#b91c1c",
            "--accent-soft": "rgba(220, 38, 38, .1)",
            "--manuel-quote-border": "rgba(30, 27, 75, .55)",
            "--manuel-h3": "#1e1b4b",
            "--manuel-h4": "#dc2626",
            "--manuel-h5": "#5c5870",
            "--manuel-encadre-border": "#1e1b4b",
            "--secondary-soft": "rgba(30, 27, 75, .08)",
            "--secondary": "#1e1b4b",
            "--launch-stamp": "#dc2626",
            "--launch-stamp-bg": "rgba(220, 38, 38, 0.1)",
            "--border": "rgba(30, 27, 75, .14)",
            "--card": "#efeae0",
            "--radius": "0",
        },
        "body_bg": """  background-color: var(--bg);
  background-image:
    url("./media/palimpseste-ink.svg"),
    linear-gradient(180deg, rgba(239, 234, 224, .92) 0%, transparent 35%);
  background-size: 480px 480px, auto;
  background-position: 70% -5%, 0 0;
  background-attachment: fixed, scroll;""",
        "extra": """
/* —— Palimpseste (lot 3 · carte blanche) —— */
.site-nav {
  background: rgba(239, 234, 224, .94);
  border-bottom: none;
  box-shadow:
    0 1px 0 var(--ink),
    0 3px 0 rgba(220, 38, 38, .45),
    0 4px 0 rgba(30, 27, 75, .2);
}
.site-nav-kicker {
  color: var(--accent);
  letter-spacing: .22em;
  font-weight: 600;
}
.site-nav-product {
  font-weight: 600;
  font-style: italic;
}
.site-nav-links > a.is-active {
  color: var(--accent);
  font-style: italic;
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: .3em;
}
.site-hero-kicker {
  color: var(--accent);
  letter-spacing: .2em;
}
.site-title {
  font-weight: 600;
  letter-spacing: -.03em;
  text-shadow: 2px 2px 0 rgba(220, 38, 38, .08);
}
.site-title-hero {
  font-size: clamp(2.6rem, 7vw, 4.2rem);
  line-height: .95;
}
.site-title-hero em {
  font-style: italic;
  color: var(--accent);
  position: relative;
}
.site-title-hero em::after {
  content: "";
  position: absolute;
  left: -.05em; right: -.05em; bottom: .08em;
  height: .35em;
  background: rgba(220, 38, 38, .12);
  z-index: -1;
}
.home-amphitheatre .home-hero-copy::after {
  content: "";
  display: block;
  margin-top: 1.75rem;
  width: min(100%, 24rem);
  aspect-ratio: 4 / 3;
  background: url("./media/palimpseste-hero.svg") center / cover no-repeat;
  box-shadow:
    6px 6px 0 rgba(30, 27, 75, .08),
    inset 0 0 0 1px rgba(30, 27, 75, .2);
}
.home-rule {
  height: 2px;
  background:
    linear-gradient(90deg, var(--ink), transparent 70%),
    repeating-linear-gradient(90deg, var(--accent) 0 3px, transparent 3px 8px);
  background-size: 100% 1px, 100% 1px;
  background-position: 0 0, 0 100%;
  background-repeat: no-repeat;
  opacity: 1;
}
.ex-item {
  background: transparent;
  border: none;
  border-bottom: 1px solid var(--border);
  position: relative;
  padding-left: 1.1rem;
}
.ex-item::before {
  content: "※";
  position: absolute;
  left: 0; top: 1.1rem;
  color: var(--accent);
  font-size: .85rem;
  opacity: .7;
}
.ex-item:hover {
  background: rgba(30, 27, 75, .03);
  transform: none;
  box-shadow: none;
  border-bottom-color: var(--ink);
}
.ex-item-type {
  color: var(--accent);
  font-style: italic;
  letter-spacing: .08em;
  text-transform: none;
  font-weight: 600;
}
.ex-item-cta { color: var(--ink); font-style: italic; }
.home-access-card {
  background: var(--card);
  border: 1px solid var(--ink);
  box-shadow: 4px 4px 0 rgba(220, 38, 38, .15);
  border-radius: 0;
}
.home-access-card.is-accent {
  background: #fff;
  box-shadow: 6px 6px 0 rgba(30, 27, 75, .18);
}
.btn { border-radius: 0; }
.btn.fill-secondary {
  background: var(--ink);
  color: #efeae0;
  font-weight: 600;
}
.btn.outline-accent {
  border: 1px solid var(--accent);
  color: var(--accent);
  font-weight: 600;
}
.manuel-nav-side {
  border-right: 1px solid var(--border);
  background:
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 27px,
      rgba(30, 27, 75, .04) 27px,
      rgba(30, 27, 75, .04) 28px
    );
}
.manuel-prose h3 {
  font-style: italic;
  border-bottom: 1px solid rgba(220, 38, 38, .25);
  padding-bottom: .25rem;
}
blockquote, .manuel-prose blockquote {
  border: none;
  border-top: 1px solid var(--ink);
  border-bottom: 1px solid var(--ink);
  background: transparent;
  font-family: var(--font-display);
  font-style: italic;
  font-size: 1.15em;
  padding: 1rem 0;
}
.encadre {
  border: 1px dashed var(--ink);
  background: rgba(220, 38, 38, .04);
  position: relative;
}
.encadre::before {
  content: "marginalia";
  position: absolute;
  top: -.55rem; left: .75rem;
  padding: 0 .35rem;
  font-size: .62rem;
  letter-spacing: .14em;
  text-transform: uppercase;
  background: var(--bg);
  color: var(--accent);
}
.site-footer {
  border-top: 1px solid var(--ink);
  background: var(--bg-elevated);
}
""",
    },
    "site-amphitheatre.css": {
        "lot": "3 · carte blanche",
        "label": "Amphithéâtre",
        "tagline": "Wunderkammer : vert forêt, laiton, cadres ornés — curiosités et prestige particulier.",
        "fonts": (
            "https://fonts.googleapis.com/css2?"
            "family=Bodoni+Moda:ital,opsz,wght@0,6..96,500;0,6..96,700;1,6..96,500"
            "&family=Commissioner:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap"
        ),
        "font_ui": '"Commissioner", system-ui, sans-serif',
        "font_display": '"Bodoni Moda", "Times New Roman", serif',
        "root": {
            "--bg": "#0c1f14",
            "--bg-elevated": "#132a1c",
            "--ink": "#e8e2d4",
            "--muted": "#9aaf9e",
            "--accent": "#d4a84b",
            "--accent-hover": "#e6c06a",
            "--accent-soft": "rgba(212, 168, 75, .14)",
            "--manuel-quote-border": "rgba(212, 168, 75, .7)",
            "--manuel-h3": "#d4a84b",
            "--manuel-h4": "#e8e2d4",
            "--manuel-h5": "#9aaf9e",
            "--manuel-encadre-border": "#d4a84b",
            "--secondary-soft": "rgba(124, 45, 58, .2)",
            "--secondary": "#a84d5c",
            "--launch-stamp": "#d4a84b",
            "--launch-stamp-bg": "rgba(212, 168, 75, 0.12)",
            "--border": "rgba(232, 226, 212, .14)",
            "--card": "#132a1c",
            "--radius": "2px",
        },
        "body_bg": """  background-color: var(--bg);
  background-image:
    url("./media/cabinet-ornament.svg"),
    radial-gradient(ellipse 70% 50% at 80% 10%, rgba(212, 168, 75, .12) 0%, transparent 55%),
    radial-gradient(ellipse 50% 40% at 10% 90%, rgba(26, 61, 40, .9) 0%, transparent 50%),
    linear-gradient(180deg, #0f2618 0%, #0c1f14 100%);
  background-size: 200px 200px, auto, auto, auto;
  background-attachment: fixed;""",
        "extra": """
/* —— Amphithéâtre (lot 3 · carte blanche) —— */
.site-nav {
  background: rgba(12, 31, 20, .92);
  border-bottom: 1px solid rgba(212, 168, 75, .35);
  box-shadow: inset 0 -1px 0 rgba(212, 168, 75, .15);
}
.site-nav-kicker {
  color: var(--accent);
  letter-spacing: .2em;
  font-weight: 600;
}
.site-nav-product {
  font-weight: 500;
  letter-spacing: .02em;
}
.site-nav-links > a.is-active {
  color: var(--accent);
  border-bottom: 1px solid var(--accent);
}
.site-hero-kicker {
  color: var(--accent);
  letter-spacing: .18em;
}
.site-title {
  font-weight: 500;
  letter-spacing: -.01em;
}
.site-title-hero em {
  font-style: italic;
  color: var(--accent);
}
.home-amphitheatre .home-hero {
  gap: 2rem;
}
.home-rule {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
  opacity: .7;
  position: relative;
}
.home-rule::before,
.home-rule::after {
  content: "◆";
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  color: var(--accent);
  font-size: .55rem;
  opacity: .8;
}
.home-rule::before { left: 0; }
.home-rule::after { right: 0; }
.ex-item {
  background: linear-gradient(160deg, rgba(19, 42, 28, .95), rgba(12, 31, 20, .7));
  border: 1px solid rgba(212, 168, 75, .22);
  border-radius: 2px;
  transition: border-color .18s ease, box-shadow .18s ease;
}
.ex-item:hover {
  border-color: rgba(212, 168, 75, .55);
  box-shadow: 0 0 0 1px rgba(212, 168, 75, .2), 0 12px 36px rgba(0, 0, 0, .3);
  transform: none;
}
.ex-item-type {
  color: var(--accent);
  letter-spacing: .14em;
  font-weight: 600;
}
.ex-item-cta { color: var(--accent); }
.home-access-card {
  background: var(--card);
  border: 1px solid rgba(212, 168, 75, .3);
  position: relative;
}
.home-access-card::before {
  content: "";
  position: absolute;
  inset: 5px;
  border: 1px solid rgba(212, 168, 75, .18);
  pointer-events: none;
}
.home-access-card.is-accent {
  background: linear-gradient(145deg, rgba(212, 168, 75, .1), rgba(19, 42, 28, .9));
  border-color: rgba(212, 168, 75, .5);
}
.btn.fill-secondary {
  background: var(--accent);
  color: #0c1f14;
  font-weight: 700;
  border-radius: 2px;
}
.btn.outline-accent {
  border-color: var(--accent);
  color: var(--accent);
  border-radius: 2px;
}
.manuel-nav-side {
  border-right: 1px solid rgba(212, 168, 75, .2);
  background: rgba(0, 0, 0, .15);
}
.manuel-nav-side a.is-current {
  color: var(--accent);
  border-left: 2px solid var(--accent);
  padding-left: .6rem;
}
blockquote, .manuel-prose blockquote {
  border-color: var(--accent);
  background: rgba(212, 168, 75, .06);
  font-family: var(--font-display);
  font-style: italic;
}
.encadre {
  border: 1px solid rgba(212, 168, 75, .4);
  background: rgba(212, 168, 75, .05);
  box-shadow: inset 0 0 0 4px rgba(12, 31, 20, .5);
}
.site-footer {
  border-top: 1px solid rgba(212, 168, 75, .3);
  background: #0a1a11;
}
.site-footer-brand { color: var(--accent); }
@keyframes amphitheatre-glow {
  0%, 100% { opacity: .65; }
  50% { opacity: 1; }
}
.site-nav-kicker { animation: amphitheatre-glow 5s ease-in-out infinite; }
""",
    },
}

THEMES = {**LOT1, **LOT2, **LOT3}

# Motifs graphiques de fond (droite) — hors thèmes Accessibilité
def _motif(
    asset: str,
    *,
    opacity: float = 0.58,
    width: str = "min(440px, 40vw)",
    height: str = "min(580px, 88vh)",
    top: str = "6%",
    right: str = "0",
    position: str = "right center",
    filt: str = "",
) -> str:
    filt_line = f"  filter: {filt};\n" if filt else ""
    return f"""
/* —— Motif de fond (droite) —— */
.reading-lamp {{
  display: block !important;
  position: fixed;
  right: {right};
  top: {top};
  width: {width};
  height: {height};
  background: url("./media/{asset}") {position} / contain no-repeat;
  opacity: {opacity};
  z-index: 0;
  pointer-events: none;
{filt_line}  -webkit-mask-image: linear-gradient(90deg, transparent 0%, #000 22%, #000 100%);
  mask-image: linear-gradient(90deg, transparent 0%, #000 22%, #000 100%);
}}
.site-nav, .site-main, .site-footer, .theme-lab {{
  position: relative;
  z-index: 2;
}}
.site-main {{
  max-width: calc(100% - min(240px, 24vw));
}}
@media (max-width: 720px) {{
  .reading-lamp {{
    opacity: {max(0.32, opacity - 0.22):.2f};
    width: 170px;
    height: 220px;
    top: auto;
    bottom: 3%;
  }}
  .site-main {{ max-width: 100%; }}
}}
""".rstrip()


THEME_MOTIFS = {
    "site-campus.css": _motif(
        "motif-campus.png",
        opacity=0.72,
        width="min(560px, 48vw)",
        height="min(460px, 75vh)",
        top="12%",
        right="clamp(0.25rem, 1vw, 1rem)",
        filt="saturate(.95) contrast(1.05)",
    ),
    "site-amphitheatre.css": _motif(
        "motif-amphitheatre.svg",
        opacity=0.7,
        width="min(480px, 44vw)",
        height="min(660px, 92vh)",
        top="2%",
        right="clamp(0.25rem, 1vw, 1rem)",
        filt="drop-shadow(0 0 28px rgba(212, 168, 75, .22))",
    ),
    "site-salle-td.css": _motif(
        "motif-salle-td.png",
        opacity=0.78,
        width="min(500px, 46vw)",
        height="min(440px, 75vh)",
        top="10%",
        right="clamp(0.25rem, 1vw, 1rem)",
        filt="saturate(1.08)",
    ),
    "site-salle-lecture.css": _motif(
        "motif-salle-lecture.png",
        opacity=0.62,
        width="min(440px, 40vw)",
        height="min(640px, 94vh)",
        top="0",
        right="clamp(0.25rem, 1vw, 1rem)",
        filt="saturate(.92) contrast(1.05)",
    ),
    "site-salle-lecture-nuit.css": _motif(
        "motif-salle-lecture-nuit.png",
        opacity=0.68,
        width="min(440px, 40vw)",
        height="min(580px, 90vh)",
        top="2%",
        right="clamp(0.25rem, 1vw, 1rem)",
        filt="brightness(1.08) saturate(.9)",
    ),
}

# Variantes « Salle de lecture · Nuit » + lampe à droite (4 propositions)
LAMP_OVERLAYS = {
    "site-salle-lecture-nuit-lampe-spirale.css": {
        "label": "Lampe Spirale",
        "css": """
/* —— Lampe Spirale (nuit) —— */
.reading-lamp { display: block !important; }
.reading-lamp {
  position: fixed;
  right: clamp(0.5rem, 2vw, 1.5rem);
  bottom: 8%;
  width: min(280px, 34vw);
  height: min(480px, 82vh);
  background: url("./media/lamp-spirale.svg") right bottom / contain no-repeat;
  z-index: 30;
  pointer-events: none;
  filter: drop-shadow(0 0 36px rgba(255, 210, 120, .55));
}
body.site-body::before {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 60% 75% at 82% 68%, rgba(255, 210, 130, .32) 0%, transparent 58%),
    radial-gradient(ellipse 50% 55% at 62% 58%, rgba(255, 236, 190, .14) 0%, transparent 60%);
}
.site-nav, .site-main, .site-footer, .theme-lab {
  position: relative;
  z-index: 2;
}
.site-main {
  max-width: calc(100% - min(300px, 34vw));
}
@media (max-width: 720px) {
  .reading-lamp { opacity: .65; width: 140px; height: 260px; }
  .site-main { max-width: 100%; }
}
""",
    },
    "site-salle-lecture-nuit-lampe-courbe.css": {
        "label": "Lampe Courbe",
        "css": """
/* —— Lampe Courbe (nuit) —— */
.reading-lamp { display: block !important; }
.reading-lamp {
  position: fixed;
  right: 0;
  bottom: 4%;
  width: min(320px, 38vw);
  height: min(500px, 88vh);
  background: url("./media/lamp-courbe.svg") right bottom / contain no-repeat;
  z-index: 30;
  pointer-events: none;
  filter: drop-shadow(0 0 28px rgba(255, 255, 255, .35));
}
body.site-body::before {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 55% 60% at 74% 55%, rgba(255, 255, 255, .28) 0%, transparent 55%),
    radial-gradient(ellipse 40% 45% at 58% 60%, rgba(220, 235, 255, .12) 0%, transparent 60%);
}
.site-nav, .site-main, .site-footer, .theme-lab {
  position: relative;
  z-index: 2;
}
.site-main {
  max-width: calc(100% - min(320px, 36vw));
}
@media (max-width: 720px) {
  .reading-lamp { opacity: .6; width: 150px; height: 260px; }
  .site-main { max-width: 100%; }
}
""",
    },
    "site-salle-lecture-nuit-lampe-ampoule.css": {
        "label": "Lampe Ampoule",
        "css": """
/* —— Lampe Ampoule (nuit) —— */
.reading-lamp { display: block !important; }
.reading-lamp {
  position: fixed;
  right: clamp(1.5rem, 5vw, 4rem);
  top: 5rem;
  width: min(220px, 28vw);
  height: min(340px, 62vh);
  background: url("./media/lamp-ampoule.svg") center top / contain no-repeat;
  z-index: 30;
  pointer-events: none;
  filter: drop-shadow(0 0 48px rgba(200, 220, 255, .75));
  animation: lamp-ampoule-pulse 5s ease-in-out infinite;
}
@keyframes lamp-ampoule-pulse {
  0%, 100% { filter: drop-shadow(0 0 36px rgba(200, 220, 255, .55)); }
  50% { filter: drop-shadow(0 0 64px rgba(220, 235, 255, .9)); }
}
body.site-body::before {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 52% 58% at 82% 26%, rgba(230, 240, 255, .38) 0%, transparent 55%),
    radial-gradient(ellipse 58% 65% at 68% 48%, rgba(180, 205, 255, .14) 0%, transparent 65%);
}
.site-nav, .site-main, .site-footer, .theme-lab {
  position: relative;
  z-index: 2;
}
.site-main {
  max-width: calc(100% - min(240px, 30vw));
  padding-right: 1rem;
}
@media (max-width: 720px) {
  .reading-lamp { opacity: .65; width: 120px; height: 190px; top: 5rem; }
  .site-main { max-width: 100%; }
}
""",
    },
    "site-salle-lecture-nuit-lampe-banquier.css": {
        "label": "Lampe Banquier",
        "css": """
/* —— Lampe Banquier (nuit) —— */
.reading-lamp { display: block !important; }
.reading-lamp {
  position: fixed;
  right: clamp(1.5rem, 4vw, 3.5rem);
  top: 12%;
  width: min(380px, 34vw);
  height: min(480px, 78vh);
  background: url("./media/lamp-banquier.png?v=left") center center / contain no-repeat;
  z-index: 30;
  pointer-events: none;
  filter: drop-shadow(0 0 18px rgba(40, 140, 80, .35));
}
body.site-body::before {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 40% 36% at 86% 48%, rgba(255, 236, 180, .34) 0%, transparent 58%),
    radial-gradient(ellipse 26% 24% at 90% 44%, rgba(60, 150, 90, .14) 0%, transparent 55%),
    radial-gradient(ellipse 48% 46% at 74% 58%, rgba(255, 248, 220, .12) 0%, transparent 65%);
}
.site-nav, .site-main, .site-footer, .theme-lab {
  position: relative;
  z-index: 2;
}
.site-main {
  max-width: calc(100% - min(320px, 36vw));
}
.site-main .manuel-content,
.site-main .home-hero-copy,
.site-main .legal-prose {
  text-shadow: 0 0 24px rgba(255, 236, 180, .1);
}
@media (max-width: 720px) {
  .reading-lamp { opacity: .7; width: 160px; height: 230px; top: auto; bottom: 4%; }
  .site-main { max-width: 100%; }
}
""",
    },
}


def patch_root(css: str, theme: dict) -> str:
    lot = theme.get("lot", "")
    header = f"/* Thème universitaire — {theme['label']} (Lot {lot}) */"
    lines = [header, ":root {"]
    for key, val in theme["root"].items():
        lines.append(f"  {key}: {val};")
    lines.extend(
        [
            "  --read-column: 46rem;",
            f"  --font-ui: {theme['font_ui']};",
            f"  --font-display: {theme['font_display']};",
            "  --nav-h: 3.5rem;",
            "  --ok: #6ee7b7;",
            "  --danger: #f87171;",
            "}",
        ]
    )
    new_root = "\n".join(lines)
    css = re.sub(r"/\* Site chrome.*?\*/\s*:root\s*\{[^}]+\}", new_root, css, count=1, flags=re.S)
    css = re.sub(
        r"/\* Thème universitaire[^*]*\*/\s*:root\s*\{[^}]+\}",
        new_root,
        css,
        count=1,
        flags=re.S,
    )
    css = re.sub(
        r"html, body \{[^}]+background-color:[^;]+;[^}]+background-image:[^;]+;[^}]+background-attachment:[^;]+;[^}]+\}",
        "html, body {\n  margin: 0;\n  min-height: 100%;\n  color: var(--ink);\n  font-family: var(--font-ui);\n"
        + theme["body_bg"]
        + "\n}",
        css,
        count=1,
        flags=re.S,
    )
    if "background-attachment" in css and theme["body_bg"] not in css:
        css = re.sub(
            r"html, body \{\n  margin: 0;\n  min-height: 100%;\n  color: var\(--ink\);\n  font-family: var\(--font-ui\);[^}]+\}",
            "html, body {\n  margin: 0;\n  min-height: 100%;\n  color: var(--ink);\n  font-family: var(--font-ui);\n"
            + theme["body_bg"]
            + "\n}",
            css,
            count=1,
            flags=re.S,
        )
    css = re.sub(
        r"background: rgba\(14, 20, 25, \.92\)",
        "background: var(--bg-elevated)",
        css,
    )
    return css + "\n" + theme["extra"].strip() + "\n"


def main() -> None:
    base = BASE_CSS.read_text(encoding="utf-8")
    for filename, theme in THEMES.items():
        out = patch_root(base, theme)
        if filename in THEME_MOTIFS:
            out = out.rstrip() + "\n" + THEME_MOTIFS[filename] + "\n"
        # Accessibilité : pas de motif décoratif
        if "access" in filename:
            out = out.rstrip() + "\n.reading-lamp { display: none !important; }\n"
        (OUT_DIR / filename).write_text(out, encoding="utf-8")
        print(f"OK {filename} ({len(out)} chars) — {theme['label']} (Lot {theme.get('lot', '?')})")

    # Campus = charte de production actuelle (ex-Amphithéâtre)
    campus = base.replace(
        "/* Site chrome — thème Campus (encre, or, Cormorant / DM Sans) */",
        "/* Thème universitaire — Campus (production · encre, or, Cormorant / DM Sans) */",
        1,
    )
    campus = campus.rstrip() + "\n" + THEME_MOTIFS["site-campus.css"] + "\n"
    (OUT_DIR / "site-campus.css").write_text(campus, encoding="utf-8")
    print(f"OK site-campus.css ({len(campus)} chars) — Campus (production)")

    # Lampes sur Salle de lecture · Nuit (remplacent le motif rayonnage)
    nuit_path = OUT_DIR / "site-salle-lecture-nuit.css"
    if nuit_path.exists():
        nuit_css = nuit_path.read_text(encoding="utf-8")
        for filename, lamp in LAMP_OVERLAYS.items():
            out = (
                nuit_css
                + "\n"
                + lamp["css"].strip()
                + "\n"
                + ".reading-lamp { -webkit-mask-image: none; mask-image: none; opacity: 1; }\n"
            )
            (OUT_DIR / filename).write_text(out, encoding="utf-8")
            print(f"OK {filename} — Nuit + {lamp['label']}")

    # Nettoyage des anciens noms de fichiers
    for stale in (
        "site-silence.css",
        "site-tribune.css",
        "site-cabinet.css",
        "site-salle-lecture-malvoyants.css",
    ):
        p = OUT_DIR / stale
        if p.exists():
            p.unlink()
            print(f"removed {stale}")

    write_live_themes(base)


# Thèmes live (site public) — sans motifs / lampes
LIVE_THEMES = (
    ("amphitheatre.css", "site-amphitheatre.css", "Amphithéâtre"),
    ("salle-td.css", "site-salle-td.css", "Salle de TD"),
    ("salle-lecture-jour.css", "site-salle-lecture.css", "Salle de lecture · jour"),
    ("salle-lecture-nuit.css", "site-salle-lecture-nuit.css", "Salle de lecture · nuit"),
    (
        "salle-lecture-access-jour.css",
        "site-salle-lecture-access-jour.css",
        "Salle de lecture (accessibilité) · jour",
    ),
    (
        "salle-lecture-access-nuit.css",
        "site-salle-lecture-access-nuit.css",
        "Salle de lecture (accessibilité) · nuit",
    ),
)

LIVE_DIR = ROOT / "site" / "templates" / "themes"


def _strip_decor(css: str) -> str:
    """Retire motifs / lampes / reading-lamp du CSS labo pour le site live."""
    markers = (
        "\n/* —— Motif de fond",
        "\n/* —— Lampe ",
        "\n.reading-lamp {",
    )
    cut = len(css)
    for m in markers:
        i = css.find(m)
        if i != -1:
            cut = min(cut, i)
    css = css[:cut].rstrip() + "\n"
    # Sécurité : aucune règle reading-lamp restante
    lines = []
    skip = False
    depth = 0
    for line in css.splitlines(keepends=True):
        if not skip and ".reading-lamp" in line:
            skip = True
            depth = line.count("{") - line.count("}")
            if depth <= 0 and "{" in line:
                skip = False
            continue
        if skip:
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                skip = False
            continue
        lines.append(line)
    css = "".join(lines)
    import re

    # Aucune image pour le live
    css = re.sub(r"\s*url\(\s*[\"']?\./media/[^\"')]+[\"']?\s*\)\s*,?", "", css)
    return css.rstrip() + "\n"


def write_live_themes(base: str) -> None:
    """Écrit site/templates/themes/*.css prêts pour le sélecteur live (sans images)."""
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    # Régénère chaque thème live depuis THEMES (sans motifs)
    key_by_lab = {lab: live for live, lab, _ in LIVE_THEMES}
    for filename, theme in THEMES.items():
        if filename not in key_by_lab:
            continue
        out = _strip_decor(patch_root(base, theme))
        live_name = key_by_lab[filename]
        (LIVE_DIR / live_name).write_text(out, encoding="utf-8")
        label = next(lbl for live, lab, lbl in LIVE_THEMES if lab == filename)
        print(f"LIVE {live_name} — {label} ({len(out)} chars)")

    # Manifeste JSON pour le sélecteur (Campus = site.css)
    fonts = {
        "campus": (
            "https://fonts.googleapis.com/css2?"
            "family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500"
            "&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400"
            "&display=swap"
        ),
    }
    for filename, theme in THEMES.items():
        if filename not in key_by_lab:
            continue
        live_name = key_by_lab[filename]
        slug = live_name.replace(".css", "")
        fonts[slug] = theme["fonts"]

    import json

    manifest = {
        "default": "campus",
        "themes": [
            {
                "id": "campus",
                "label": "Campus",
                "css": "site.css",
                "fonts": fonts["campus"],
            },
            {
                "id": "amphitheatre",
                "label": "Amphithéâtre",
                "css": "themes/amphitheatre.css",
                "fonts": fonts["amphitheatre"],
            },
            {
                "id": "salle-td",
                "label": "Salle de TD",
                "css": "themes/salle-td.css",
                "fonts": fonts["salle-td"],
            },
            {
                "id": "salle-lecture-jour",
                "label": "Salle de lecture · jour",
                "css": "themes/salle-lecture-jour.css",
                "fonts": fonts["salle-lecture-jour"],
            },
            {
                "id": "salle-lecture-nuit",
                "label": "Salle de lecture · nuit",
                "css": "themes/salle-lecture-nuit.css",
                "fonts": fonts["salle-lecture-nuit"],
            },
            {
                "id": "salle-lecture-access-jour",
                "label": "Salle de lecture (accessibilité) · jour",
                "css": "themes/salle-lecture-access-jour.css",
                "fonts": fonts["salle-lecture-access-jour"],
            },
            {
                "id": "salle-lecture-access-nuit",
                "label": "Salle de lecture (accessibilité) · nuit",
                "css": "themes/salle-lecture-access-nuit.css",
                "fonts": fonts["salle-lecture-access-nuit"],
            },
        ],
    }
    (LIVE_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"LIVE manifest.json ({len(manifest['themes'])} thèmes)")


if __name__ == "__main__":
    main()
