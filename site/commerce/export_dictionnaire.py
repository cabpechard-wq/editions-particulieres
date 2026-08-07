"""Convertit notion_to_word/output/glossaire.html → site /dictionnaire/.

Usage :
  python commerce/export_dictionnaire.py
  python commerce/export_dictionnaire.py --src chemin/glossaire.html
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import unicodedata
from pathlib import Path

COMMERCE = Path(__file__).resolve().parent
DEFAULT_SRC = Path(r"C:\Users\anton\Desktop\notion_to_word\output\glossaire.html")
TEMPLATES = COMMERCE / "templates"
SITE = COMMERCE / "dist" / "site"
HOST = COMMERCE / "host-repo"
OUT_NAME = "dictionnaire"

META_RE = re.compile(
    r"^(Fiches?\b|Ressources complémentaires|Manuel\s*:|Méthode\s*:|Formule\s*:|Sommaire|glossaire)\s*",
    re.I,
)
SKIP_HEAD = {"glossaire", "sommaire"}
TITLE_RE = re.compile(r'<h1[^>]*class="site-title"[^>]*>(.*?)</h1>', re.I | re.S)


def strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).replace("\xa0", " ").strip()


def norm_title(s: str) -> str:
    t = strip_tags(s).lower().replace("’", "'")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def slugify(term: str) -> str:
    s = unicodedata.normalize("NFKD", term)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "entree"


def letter_key(term: str) -> str:
    s = unicodedata.normalize("NFKD", term)
    s = "".join(c for c in s if not unicodedata.combining(c))
    ch = (s[:1] or "#").upper()
    return ch if "A" <= ch <= "Z" else "#"


def build_manuel_title_map(manuel_roots: list[Path]) -> dict[str, str]:
    """title normalisé → chemin relatif depuis /dictionnaire/."""
    out: dict[str, str] = {}
    for root in manuel_roots:
        if not root.exists():
            continue
        for p in root.rglob("index.html"):
            if "_aside" in p.parts:
                continue
            rel = p.parent.relative_to(root).as_posix()
            if rel == ".":
                continue
            txt = p.read_text(encoding="utf-8")
            m = TITLE_RE.search(txt)
            if not m:
                continue
            title = strip_tags(m.group(1))
            key = norm_title(title)
            href = f"../manuel/{rel}/"
            out[key] = href
            # variantes typographiques fréquentes
            out[key.replace("'", "’")] = href
            out[key.replace("’", "'")] = href
    return out


def resolve_manuel_href(href: str, link_text: str, title_map: dict[str, str]) -> str | None:
    """Résout un lien Manuel (Notion ou chemin local) vers le site."""
    key = norm_title(link_text)
    if key in title_map:
        return title_map[key]

    href = (href or "").strip().replace("\\", "/")
    if not href or href.endswith(".docx"):
        return None

    # chemin local contenant dp-XXX
    m = re.search(r"(dp-\d+(?:/dp-\d+)*)", href)
    if m:
        digits_path = m.group(1)
        # cherche une page locale qui se termine par ce chemin
        for dest in title_map.values():
            if dest.rstrip("/").endswith(digits_path):
                return dest
        # fallback : préfixer dp-000 si besoin
        if not digits_path.startswith("dp-000"):
            return f"../manuel/dp-000/{digits_path}/"
        return f"../manuel/{digits_path}/"

    return None


def clean_manuel_para(raw_p: str, title_map: dict[str, str]) -> str:
    """Ne conserve que la ligne Manuel, liens résolus vers le site."""

    def repl(m: re.Match[str]) -> str:
        href = m.group(1)
        inner = strip_tags(m.group(2))
        local = resolve_manuel_href(href, inner, title_map)
        text = inner or strip_tags(href)
        if local:
            return f'<a href="{html.escape(local, quote=True)}">{html.escape(text)}</a>'
        return html.escape(text)

    return re.sub(r'<a\s+href="([^"]*)"[^>]*>(.*?)</a>', repl, raw_p, flags=re.I | re.S)


def parse_entries(raw: str, title_map: dict[str, str]) -> list[dict]:
    paras = re.findall(r"<p>(.*?)</p>", raw, flags=re.I | re.S)
    texts = [strip_tags(p) for p in paras]
    raws = paras
    entries: list[dict] = []
    i = 0
    while i < len(texts):
        t = texts[i]
        if not t or t.lower() in SKIP_HEAD or META_RE.match(t):
            i += 1
            continue
        if (
            i + 1 < len(texts)
            and texts[i + 1]
            and not META_RE.match(texts[i + 1])
            and len(texts[i + 1]) > 40
        ):
            term = t
            definition = texts[i + 1]
            i += 2
            extras: list[str] = []
            while i < len(texts) and texts[i] and META_RE.match(texts[i]):
                line = texts[i]
                raw_line = raws[i]
                if line.lower().startswith("manuel"):
                    cleaned = clean_manuel_para(raw_line, title_map)
                    # ne garder que s'il reste un vrai lien
                    if "<a href=" in cleaned:
                        extras.append(f'<p class="dict-extra">{cleaned}</p>')
                # Fiches / Méthode / Formule / Ressources : ignorés
                i += 1
            entries.append(
                {
                    "term": term,
                    "definition": definition,
                    "extras_html": "\n".join(extras),
                    "slug": slugify(term),
                    "letter": letter_key(term),
                }
            )
            continue
        i += 1

    seen: dict[str, int] = {}
    for e in entries:
        base = e["slug"]
        n = seen.get(base, 0)
        seen[base] = n + 1
        if n:
            e["slug"] = f"{base}-{n + 1}"
    return entries


def render_body(entries: list[dict]) -> tuple[str, str]:
    letters = sorted({e["letter"] for e in entries if e["letter"] != "#"}) + (
        ["#"] if any(e["letter"] == "#" for e in entries) else []
    )
    index = ['<nav class="dict-index" aria-label="Index alphabétique">']
    for L in letters:
        index.append(f'<a href="#lettre-{html.escape(L)}">{html.escape(L)}</a>')
    index.append("</nav>")

    by_letter: dict[str, list[dict]] = {}
    for e in entries:
        by_letter.setdefault(e["letter"], []).append(e)

    blocks = [
        '<p class="dict-toolbar">'
        '<label class="sr-only" for="dict-filter">Filtrer</label>'
        '<input id="dict-filter" type="search" placeholder="Filtrer une entrée…" autocomplete="off">'
        "</p>",
        '<div class="dict-entries">',
    ]
    for L in letters:
        blocks.append(
            f'<section class="dict-letter" id="lettre-{html.escape(L)}" data-letter="{html.escape(L)}">'
        )
        blocks.append(f'<h2 class="dict-letter-title">{html.escape(L)}</h2>')
        for e in by_letter.get(L, []):
            blocks.append(
                f'<article class="dict-entry" id="{html.escape(e["slug"])}" '
                f'data-term="{html.escape(e["term"].lower())}">'
                f'<h3 class="dict-term">{html.escape(e["term"])}</h3>'
                f'<p class="dict-def">{html.escape(e["definition"])}</p>'
            )
            if e["extras_html"]:
                blocks.append(e["extras_html"])
            blocks.append("</article>")
        blocks.append("</section>")
    blocks.append("</div>")
    return "\n".join(index), "\n".join(blocks)


FILTER_JS = """
<script>
(function () {
  const input = document.getElementById("dict-filter");
  if (!input) return;
  const entries = Array.from(document.querySelectorAll(".dict-entry"));
  const sections = Array.from(document.querySelectorAll(".dict-letter"));
  input.addEventListener("input", () => {
    const q = (input.value || "").trim().toLowerCase();
    entries.forEach((el) => {
      const ok = !q || (el.getAttribute("data-term") || "").includes(q)
        || (el.textContent || "").toLowerCase().includes(q);
      el.hidden = !ok;
    });
    sections.forEach((sec) => {
      const any = Array.from(sec.querySelectorAll(".dict-entry")).some((e) => !e.hidden);
      sec.hidden = !any;
    });
  });
})();
</script>
"""


def build(src: Path, out_dirs: list[Path]) -> int:
    if not src.exists():
        raise SystemExit(f"Source introuvable : {src}")

    title_map = build_manuel_title_map(
        [HOST / "manuel", SITE / "manuel"]
    )
    if not title_map:
        print("Attention : aucune page Manuel trouvée pour résoudre les liens.")

    raw = src.read_text(encoding="utf-8")
    entries = parse_entries(raw, title_map)
    if not entries:
        raise SystemExit("Aucune entrée parsée.")

    # stats liens
    linked = sum(1 for e in entries if e["extras_html"])
    print(f"Entrées avec lien(s) Manuel : {linked}/{len(entries)} (map titres={len(title_map)})")

    tpl = (TEMPLATES / "dictionnaire.html").read_text(encoding="utf-8")
    index_html, body_html = render_body(entries)
    page = (
        tpl.replace("{{ENTRY_COUNT}}", str(len(entries)))
        .replace("{{DICT_INDEX}}", index_html)
        .replace("{{DICT_BODY}}", body_html)
        .replace("{{FILTER_JS}}", FILTER_JS)
    )

    for root in out_dirs:
        if not root.exists():
            continue
        dst = root / OUT_NAME
        dst.mkdir(parents=True, exist_ok=True)
        (dst / "index.html").write_text(page, encoding="utf-8")
        print(f"Écrit : {dst / 'index.html'} ({len(entries)} entrées)")
    return len(entries)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC)
    args = ap.parse_args()
    for root in (SITE, HOST):
        if root.exists():
            for asset in ("site.css", "site-nav.js"):
                src_a = TEMPLATES / asset
                if src_a.exists():
                    shutil.copy2(src_a, root / asset)
    n = build(args.src, [SITE, HOST])
    print(f"Dictionnaire juridique : {n} entrées.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
