"""Construit search-index.json à partir de site/dist/site (manuel, dictionnaire, arrêts).

Usage :
  python site/build_search_index.py
  python site/build_search_index.py --root site/dist/site
"""

from __future__ import annotations

import argparse
import html as html_mod
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = Path(__file__).resolve().parent / "dist" / "site"

# Limite de texte indexé par document (garde l'index léger)
MAX_TEXT = 1800
MAX_EXCERPT = 180

WHITESPACE_RE = re.compile(r"\s+")
SCRIPT_STYLE_RE = re.compile(
    r"<(script|style|nav|header|footer)\b[^>]*>.*?</\1>",
    re.I | re.S,
)


class _TextCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip = 0
        self.parts: list[str] = []
        self.title = ""
        self._in_title = False
        self._in_h1 = False
        self.h1 = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        if t in ("script", "style", "nav", "header", "footer", "noscript"):
            self._skip += 1
            return
        if self._skip:
            return
        if t == "title":
            self._in_title = True
        if t == "h1":
            self._in_h1 = True
            self.h1 = ""

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in ("script", "style", "nav", "header", "footer", "noscript"):
            if self._skip:
                self._skip -= 1
            return
        if t == "title":
            self._in_title = False
        if t == "h1":
            self._in_h1 = False

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        if self._in_title:
            self.title += data
        if self._in_h1:
            self.h1 += data
        if data and data.strip():
            self.parts.append(data)


def _norm_space(s: str) -> str:
    return WHITESPACE_RE.sub(" ", (s or "").strip())


def _plain_text(html: str) -> tuple[str, str, str]:
    """Retourne (title, h1, body_text)."""
    cleaned = SCRIPT_STYLE_RE.sub(" ", html)
    p = _TextCollector()
    try:
        p.feed(cleaned)
        p.close()
    except Exception:
        pass
    title = _norm_space(html_mod.unescape(p.title))
    h1 = _norm_space(html_mod.unescape(p.h1))
    body = _norm_space(html_mod.unescape(" ".join(p.parts)))
    return title, h1, body


def _rel_url(root: Path, path: Path, fragment: str = "") -> str:
    rel = path.relative_to(root).as_posix()
    if rel.endswith("/index.html"):
        rel = rel[: -len("index.html")]
    elif rel == "index.html":
        rel = ""
    if fragment:
        return f"{rel}#{fragment}"
    return rel


def _doc(
    *,
    doc_id: str,
    section: str,
    title: str,
    url: str,
    text: str,
) -> dict:
    text = _norm_space(text)[:MAX_TEXT]
    excerpt = text[:MAX_EXCERPT]
    if len(text) > MAX_EXCERPT:
        excerpt = excerpt.rsplit(" ", 1)[0] + "…"
    return {
        "id": doc_id,
        "section": section,
        "title": title or doc_id,
        "url": url,
        "text": text,
        "excerpt": excerpt,
    }


def index_manuel(root: Path) -> list[dict]:
    base = root / "manuel"
    if not base.is_dir():
        return []
    docs: list[dict] = []
    for path in sorted(base.rglob("index.html")):
        # _aside = actualités hors parcours principal — on indexe quand même (utile)
        html = path.read_text(encoding="utf-8", errors="ignore")
        title, h1, body = _plain_text(html)
        label = h1 or title or path.parent.name
        # Préférer le corps de l'article si présent
        m = re.search(
            r'<article[^>]*class="[^"]*manuel-prose[^"]*"[^>]*>(.*?)</article>',
            html,
            re.I | re.S,
        )
        if m:
            _, _, article = _plain_text(m.group(1))
            if article:
                body = article
        url = _rel_url(root, path)
        docs.append(
            _doc(
                doc_id=f"manuel:{url}",
                section="manuel",
                title=label,
                url=url,
                text=f"{label}. {body}",
            )
        )
    return docs


def index_dictionnaire(root: Path) -> list[dict]:
    path = root / "dictionnaire" / "index.html"
    if not path.is_file():
        return []
    html = path.read_text(encoding="utf-8", errors="ignore")
    docs: list[dict] = []
    # article.dict-entry id="…" … h3.dict-term … .dict-def
    for m in re.finditer(
        r'<article\b([^>]*)class="[^"]*\bdict-entry\b[^"]*"([^>]*)>(.*?)</article>',
        html,
        re.I | re.S,
    ):
        attrs = m.group(1) + m.group(2)
        block = m.group(3)
        id_m = re.search(r'\bid="([^"]+)"', attrs)
        term_m = re.search(
            r'<h3[^>]*class="[^"]*\bdict-term\b[^"]*"[^>]*>(.*?)</h3>',
            block,
            re.I | re.S,
        )
        def_m = re.search(
            r'<div[^>]*class="[^"]*\bdict-def\b[^"]*"[^>]*>(.*?)</div>',
            block,
            re.I | re.S,
        )
        frag = id_m.group(1) if id_m else ""
        term = _norm_space(_plain_text(term_m.group(1))[2]) if term_m else frag
        definition = _norm_space(_plain_text(def_m.group(1))[2]) if def_m else ""
        if not term and not definition:
            continue
        url = _rel_url(root, path, frag)
        docs.append(
            _doc(
                doc_id=f"dictionnaire:{frag or term}",
                section="dictionnaire",
                title=term or frag,
                url=url,
                text=f"{term}. {definition}",
            )
        )
    return docs


def index_arrets(root: Path) -> list[dict]:
    base = root / "arrets"
    if not base.is_dir():
        return []
    docs: list[dict] = []
    for path in sorted(base.rglob("index.html")):
        # Sauter la page liste (…/arrets/index.html)
        if path.parent.resolve() == base.resolve():
            continue
        html = path.read_text(encoding="utf-8", errors="ignore")
        title, h1, body = _plain_text(html)
        label = h1 or title or path.parent.name
        m = re.search(
            r'<article[^>]*class="[^"]*arrets-prose[^"]*"[^>]*>(.*?)</article>',
            html,
            re.I | re.S,
        )
        if m:
            _, _, article = _plain_text(m.group(1))
            if article:
                body = article
        # Métadonnées utiles à la recherche
        meta_bits = []
        for attr in ("data-theme", "data-juridiction", "data-reference", "data-nom"):
            am = re.search(rf'\b{attr}="([^"]*)"', html)
            if am and am.group(1).strip():
                meta_bits.append(am.group(1).strip())
        meta = " · ".join(meta_bits)
        url = _rel_url(root, path)
        docs.append(
            _doc(
                doc_id=f"arrets:{path.parent.name}",
                section="arrets",
                title=label,
                url=url,
                text=f"{label}. {meta}. {body}",
            )
        )
    return docs


def build_index(root: Path) -> dict:
    docs: list[dict] = []
    docs.extend(index_manuel(root))
    docs.extend(index_dictionnaire(root))
    docs.extend(index_arrets(root))
    counts = {
        "manuel": sum(1 for d in docs if d["section"] == "manuel"),
        "dictionnaire": sum(1 for d in docs if d["section"] == "dictionnaire"),
        "arrets": sum(1 for d in docs if d["section"] == "arrets"),
    }
    return {
        "version": 1,
        "docs": docs,
        "counts": counts,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Racine dist/site (défaut : site/dist/site)",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Fichier JSON (défaut : <root>/search-index.json)",
    )
    args = p.parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        print(f"Racine absente : {root}", file=sys.stderr)
        return 1
    out = (args.out or (root / "search-index.json")).resolve()
    data = build_index(root)
    out.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    c = data["counts"]
    print(
        f"search-index.json : {len(data['docs'])} doc(s) "
        f"(cours {c['manuel']}, dico {c['dictionnaire']}, arrets {c['arrets']}) -> {out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
